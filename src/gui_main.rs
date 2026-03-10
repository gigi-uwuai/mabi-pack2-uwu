use std::fs;
use std::path::Path;


use eframe::{egui, NativeOptions};
use rfd::FileDialog;
use regex::Regex;

mod common;
mod encryption;
mod extract;
mod list;
mod pack;
mod salt_discovery;

struct MabiPackGuiApp {
    package_folder: String,
    package_files: Vec<String>,
    selected_file_index: Option<usize>,
    output_folder: String,
    filters_input: String,
    batch_extract_all: bool,
    list_output: String,
    pack_input_folder: String,
    pack_output_folder: String,
    pack_output_name: String,
    pack_output_number: String,
    pack_compress_ext: String,
    pack_salt_keys: Vec<String>,
    pack_selected_salt_index: Option<usize>,
    status_message: String,
}

impl Default for MabiPackGuiApp {
    fn default() -> Self {
        // Load salts from salt_keys.json for the GUI dropdown.
        let (pack_salt_keys, status_message) = match salt_discovery::get_salts_for_gui() {
            Ok(keys) => {
                let msg = if keys.is_empty() {
                    "salt_keys.json is empty.".to_string()
                } else {
                    "Ready".to_string()
                };
                (keys, msg)
            }
            Err(e) => {
                (Vec::new(), format!("Load JSON error: {}", e))
            }
        };

        let pack_selected_salt_index = if pack_salt_keys.is_empty() {
            None
        } else {
            Some(0)
        };

        Self {
            package_folder: String::new(),
            package_files: Vec::new(),
            selected_file_index: None,
            output_folder: String::new(),
            filters_input: String::new(),
            batch_extract_all: false,
            list_output: String::new(),
            pack_input_folder: String::new(),
            pack_output_folder: String::new(),
            pack_output_name: String::new(),
            pack_output_number: String::new(),
            pack_compress_ext: String::new(),
            pack_salt_keys,
            pack_selected_salt_index,
            status_message,
        }
    }
}

impl MabiPackGuiApp {
    fn refresh_package_files(&mut self) {
        self.package_files.clear();
        self.selected_file_index = None;

        let folder = self.package_folder.trim();
        if folder.is_empty() {
            self.status_message = "Package folder is empty".to_string();
            return;
        }

        let path = Path::new(folder);
        if !path.is_dir() {
            self.status_message = "Package folder is not a directory".to_string();
            return;
        }

        match fs::read_dir(path) {
            Ok(entries) => {
                for entry in entries.flatten() {
                    if let Some(name) = entry.file_name().to_str() {
                        if name.to_ascii_lowercase().ends_with(".it") {
                            self.package_files.push(name.to_string());
                        }
                    }
                }

                if self.package_files.is_empty() {
                    self.status_message = "No .it files found in package folder".to_string();
                } else {
                    self.status_message =
                        format!("Found {} .it files", self.package_files.len());
                    self.selected_file_index = Some(0);
                }
            }
            Err(e) => {
                self.status_message =
                    format!("Failed to read package folder: {}", e);
            }
        }
    }

    fn selected_file_path(&self) -> Option<String> {
        let idx = self.selected_file_index?;
        let folder = self.package_folder.trim();
        if folder.is_empty() {
            return None;
        }
        let file_name = self.package_files.get(idx)?;
        let full_path = Path::new(folder).join(file_name);
        Some(full_path.to_string_lossy().into_owned())
    }

    fn run_list_selected(&mut self) {
        let Some(input_path) = self.selected_file_path() else {
            self.status_message = "No .it file selected".to_string();
            return;
        };

        // Always auto-discover the salt for the selected file.
        match salt_discovery::discover_salt_with_defaults(&input_path, Vec::<String>::new()) {
            Ok(found_salt) => {
                self.status_message = format!("Salt auto-discovered: {}", found_salt);

                match list::list_entries_for_file(&input_path, Some(found_salt.as_str())) {
                    Ok(entries) => {
                        self.list_output = entries.join("\n");
                        self.status_message = format!(
                            "Listed {} entries from {} (salt: {})",
                            entries.len(),
                            input_path,
                            found_salt
                        );
                    }
                    Err(e) => {
                        self.list_output.clear();
                        self.status_message = format!("List failed: {:?}", e);
                    }
                }
            }
            Err(e) => {
                self.list_output.clear();
                self.status_message =
                    format!("Salt auto-discovery failed: {:?}", e);
            }
        }
    }

    /// List files using the current filters across all loaded .it packages.
    /// If the filter box is empty and a file is selected, this falls back to listing
    /// only the selected package (old behavior).
    fn run_list(&mut self) {
        let filters: Vec<String> = self
            .filters_input
            .split_whitespace()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect();

        let has_filters = !filters.is_empty();

        // No filters and we have a selected file - keep old "single pack" behavior.
        if !has_filters && self.selected_file_index.is_some() {
            self.run_list_selected();
        } else {
            self.run_list_all_with_filters(filters);
        }
    }

    /// Internal helper to list entries from all .it files with optional regex filters.
    /// Each matching line is labeled with the .it file it comes from.
    fn run_list_all_with_filters(&mut self, filters: Vec<String>) {
        if self.package_files.is_empty() {
            self.status_message = "No .it files loaded to search".to_string();
            self.list_output.clear();
            return;
        }

        let folder = self.package_folder.trim();
        if folder.is_empty() {
            self.status_message = "Package folder is empty".to_string();
            self.list_output.clear();
            return;
        }

        let regexes: Option<Vec<Regex>> = if filters.is_empty() {
            None
        } else {
            match filters
                .iter()
                .map(|pat| Regex::new(pat))
                .collect::<Result<Vec<_>, _>>()
            {
                Ok(v) => Some(v),
                Err(e) => {
                    self.status_message =
                        format!("Invalid regex in filters: {}", e);
                    self.list_output.clear();
                    return;
                }
            }
        };

        let mut all_matches: Vec<String> = Vec::new();
        let mut packs_scanned = 0usize;

        for file_name in &self.package_files {
            let full_path = Path::new(folder).join(file_name);
            let full_path_str = full_path.to_string_lossy().into_owned();

            // Auto-discover salt for each pack.
            match salt_discovery::discover_salt_with_defaults(&full_path_str, Vec::<String>::new()) {
                Ok(found_salt) => {
                    match list::list_entries_for_file(
                        &full_path_str,
                        Some(found_salt.as_str()),
                    ) {
                        Ok(entries) => {
                            packs_scanned += 1;
                            for entry in entries {
                                let matched = match &regexes {
                                    Some(res) => res.iter().any(|re| re.is_match(&entry)),
                                    None => true,
                                };

                                if matched {
                                    // Label which .it file the entry comes from and which salt was used.
                                    all_matches.push(format!("{} [salt: {}] : {}", file_name, found_salt, entry));
                                }
                            }
                        }
                        Err(e) => {
                            // Keep going, but surface the last error encountered.
                            self.status_message =
                                format!("List failed for {}: {:?}", full_path_str, e);
                        }
                    }
                }
                Err(e) => {
                    // Keep going, but surface the last error encountered.
                    self.status_message = format!(
                        "Salt auto-discovery failed for {}: {:?}",
                        full_path_str, e
                    );
                }
            }
        }

        self.list_output = all_matches.join("\n");
        self.status_message = format!(
            "Found {} matching entries across {} .it files",
            all_matches.len(),
            packs_scanned
        );
    }

    fn run_extract_selected(&mut self) {
        let Some(input_path) = self.selected_file_path() else {
            self.status_message = "No .it file selected".to_string();
            return;
        };

        let output_folder = self.output_folder.trim();
        if output_folder.is_empty() {
            self.status_message = "Output folder is empty".to_string();
            return;
        }

        let filters_vec: Vec<&str> = self
            .filters_input
            .split_whitespace()
            .filter(|s| !s.is_empty())
            .collect();

        // Always auto-discover the salt for the selected file.
        match salt_discovery::discover_salt_with_defaults(&input_path, Vec::<String>::new()) {
            Ok(found_salt) => {
                self.status_message = format!(
                    "Salt auto-discovered: {}. Extracting...",
                    found_salt
                );

                match extract::run_extract_with_salt(
                    &input_path,
                    output_folder,
                    filters_vec,
                    Some(found_salt.as_str()),
                ) {
                    Ok(extracted_count) => {
                        // Show which salt was used for this extraction and how many entries matched.
                        self.list_output = format!(
                            "{} (salt: {}, extracted {} entries)",
                            input_path, found_salt, extracted_count
                        );
                        self.status_message = format!(
                            "Extracted {} entries from {} to {} (salt: {})",
                            extracted_count, input_path, output_folder, found_salt
                        );
                    }
                    Err(e) => {
                        self.status_message = format!("Extract failed: {:?}", e);
                    }
                }
            }
            Err(e) => {
                self.status_message =
                    format!("Salt auto-discovery failed: {:?}", e);
            }
        }
    }

    /// Extract using current filters across all loaded .it packages.
    fn run_extract_all(&mut self) {
        let output_folder = self.output_folder.trim();
        if output_folder.is_empty() {
            self.status_message = "Output folder is empty".to_string();
            return;
        }

        let filters_vec: Vec<&str> = self
            .filters_input
            .split_whitespace()
            .filter(|s| !s.is_empty())
            .collect();

        if self.package_files.is_empty() {
            self.status_message = "No .it files loaded to extract from".to_string();
            return;
        }

        let folder = self.package_folder.trim();
        if folder.is_empty() {
            self.status_message = "Package folder is empty".to_string();
            return;
        }

        let mut packs_extracted = 0usize;
        let mut salt_summary: Vec<String> = Vec::new();

        for file_name in &self.package_files {
            let full_path = Path::new(folder).join(file_name);
            let full_path_str = full_path.to_string_lossy().into_owned();

            match salt_discovery::discover_salt_with_defaults(&full_path_str, Vec::<String>::new()) {
                Ok(found_salt) => {
                    self.status_message = format!(
                        "Salt auto-discovered: {}. Extracting from {}...",
                        found_salt, file_name
                    );

                    match extract::run_extract_with_salt(
                        &full_path_str,
                        output_folder,
                        filters_vec.clone(),
                        Some(found_salt.as_str()),
                    ) {
                        Ok(extracted_count) => {
                            // Only record salts for packs that actually had entries matching the filters.
                            if extracted_count > 0 {
                                packs_extracted += 1;
                                salt_summary.push(format!(
                                    "{} (salt: {}, extracted {} entries)",
                                    file_name, found_salt, extracted_count
                                ));
                            }
                        }
                        Err(e) => {
                            self.status_message =
                                format!("Extract failed for {}: {:?}", full_path_str, e);
                        }
                    }
                }
                Err(e) => {
                    self.status_message = format!(
                        "Salt auto-discovery failed for {}: {:?}",
                        full_path_str, e
                    );
                }
            }
        }

        // After batch extraction, show which salts were used for .it files
        // that actually contained entries matching the filters, in the
        // list output area (the \"List output\" panel).
        self.list_output = salt_summary.join("\n");

        self.status_message = format!(
            "Batch extract completed across {} .it files into {}",
            packs_extracted, output_folder
        );
    }

    fn run_pack(&mut self) {
        let input_folder = self.pack_input_folder.trim();
        let output_folder = self.pack_output_folder.trim();
        let output_name = self.pack_output_name.trim();
        let output_number = self.pack_output_number.trim();

        if input_folder.is_empty() || output_folder.is_empty() {
            self.status_message =
                "Pack input folder and output folder are required".to_string();
            return;
        }

        if output_name.is_empty() || output_number.is_empty() {
            self.status_message =
                "Pack name and number are required".to_string();
            return;
        }

        // Name must start with a lowercase letter from e to z.
        // The rest can be mixed-case letters, numbers, or underscores.
        let name_re = Regex::new(r"^[e-z][a-zA-Z0-9_]*$").unwrap();
        if !name_re.is_match(output_name) {
            self.status_message =
                "Pack name must start with a lowercase letter (e-z) and contain only letters, numbers, or underscores.".to_string();
            return;
        }

        // Number must be 1–5 digits, representing 0–99999.
        let num_re = Regex::new(r"^[0-9]{1,5}$").unwrap();
        if !num_re.is_match(output_number) {
            self.status_message =
                "Pack number must be a numeric value between 0 and 99999 (1 to 5 digits).".to_string();
            return;
        }

        let _number_value: u32 = match output_number.parse() {
            Ok(v) if v <= 99_999 => v,
            _ => {
                self.status_message =
                    "Pack number must be a numeric value between 0 and 99999.".to_string();
                return;
            }
        };

        // Build final file name: name_number.it (no padding enforced; uses the typed digits).
        let final_name = format!("{}_{}.it", output_name, output_number);
        let out_path = Path::new(output_folder).join(&final_name);
        let out_path_str = out_path.to_string_lossy().into_owned();

        let compress_ext: Vec<&str> = self
            .pack_compress_ext
            .split(|c: char| c.is_whitespace() || c == ',')
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .collect();

        let selected_salt: Option<&str> = self
            .pack_selected_salt_index
            .and_then(|idx| self.pack_salt_keys.get(idx))
            .map(|s| s.as_str());

        // Safety check to ensure we have a valid salt before proceeding
        if selected_salt.is_none() {
            self.status_message = "No salts available! Please define them in salt_keys.json.".to_string();
            return;
        }

        match pack::run_pack_with_salt(input_folder, &out_path_str, compress_ext, selected_salt) {
            Ok(()) => {
                let salt = selected_salt.unwrap();
                self.status_message =
                    format!("Packed {} into {} (salt: {})", input_folder, out_path_str, salt);
            }
            Err(e) => {
                self.status_message = format!("Pack failed: {:?}", e);
            }
        }
    }

}


impl eframe::App for MabiPackGuiApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Top control panel with inputs and actions
        egui::TopBottomPanel::top("controls_panel")
            .resizable(false)
            .show(ctx, |ui| {
                ui.heading("Mabinogi Pack Utilities 2 - GUI");
                ui.label(
                    egui::RichText::new(
                        "Browse, inspect, extract and pack Mabinogi .it archives",
                    )
                    .small()
                    .italics()
                    .color(ui.visuals().weak_text_color()),
                );

                ui.separator();

                // Package selection
                ui.group(|ui| {
                    ui.heading("1. Select package");
                    ui.horizontal(|ui| {
                        ui.label("Package folder (contains .it files):");
                        ui.text_edit_singleline(&mut self.package_folder);
                        if ui.button("Browse…").clicked() {
                            let start_dir = if self.package_folder.trim().is_empty() {
                                "."
                            } else {
                                self.package_folder.trim()
                            };
                            if let Some(path) =
                                FileDialog::new().set_directory(start_dir).pick_folder()
                            {
                                self.package_folder = path.display().to_string();
                                self.refresh_package_files();
                            }
                        }
                        if ui.button("Reload .it files").clicked() {
                            self.refresh_package_files();
                        }
                    });

                    if !self.package_files.is_empty() {
                        ui.add_space(4.0);
                        ui.horizontal(|ui| {
                            ui.label("Select .it file:");
                            let selected_text = self
                                .selected_file_index
                                .and_then(|i| self.package_files.get(i))
                                .cloned()
                                .unwrap_or_else(|| "<none>".to_string());

                            egui::ComboBox::from_id_source("it_file_combo")
                                .selected_text(selected_text)
                                .show_ui(ui, |ui| {
                                    for (idx, name) in
                                        self.package_files.iter().enumerate()
                                    {
                                        let is_selected =
                                            self.selected_file_index == Some(idx);
                                        if ui
                                            .selectable_label(is_selected, name)
                                            .clicked()
                                        {
                                            self.selected_file_index = Some(idx);
                                        }
                                    }
                                });
                        });
                    } else {
                        ui.weak(
                            "No .it files loaded yet. Choose a folder and click \"Reload .it files\".",
                        );
                    }
                });

                ui.add_space(8.0);

                // Extract section
                ui.group(|ui| {
                    ui.heading("2. Extract files from selected .it");
                    ui.label("Output folder for extraction:");
                    ui.horizontal(|ui| {
                        ui.text_edit_singleline(&mut self.output_folder);
                        if ui.button("Browse…").clicked() {
                            let start_dir = if self.output_folder.trim().is_empty() {
                                "."
                            } else {
                                self.output_folder.trim()
                            };
                            if let Some(path) =
                                FileDialog::new().set_directory(start_dir).pick_folder()
                            {
                                self.output_folder = path.display().to_string();
                            }
                        }
                    });

                    ui.label(
                        "Extract filters (regex, space-separated, empty = all files):",
                    );
                    ui.text_edit_singleline(&mut self.filters_input);

                    ui.checkbox(
                        &mut self.batch_extract_all,
                        "Batch extract across all loaded .it files",
                    );

                    ui.add_space(4.0);
                    ui.horizontal(|ui| {
                        if ui.button("List contents").clicked() {
                            self.run_list();
                        }

                        let extract_label = if self.batch_extract_all {
                            "Extract (batch)"
                        } else {
                            "Extract (selected .it)"
                        };

                        if ui.button(extract_label).clicked() {
                            if self.batch_extract_all {
                                self.run_extract_all();
                            } else {
                                self.run_extract_selected();
                            }
                        }
                    });
                });

                ui.add_space(8.0);

                // Pack section
                ui.collapsing("3. Pack folder into .it", |ui| {
                    ui.label("Input folder to pack:");
                    ui.horizontal(|ui| {
                        ui.text_edit_singleline(&mut self.pack_input_folder);
                        if ui.button("Browse…").clicked() {
                            let start_dir = if self.pack_input_folder.trim().is_empty() {
                                "."
                            } else {
                                self.pack_input_folder.trim()
                            };
                            if let Some(path) =
                                FileDialog::new().set_directory(start_dir).pick_folder()
                            {
                                self.pack_input_folder =
                                    path.display().to_string();
                            }
                        }
                    });
                
                    ui.label("Output folder for .it file:");
                    ui.horizontal(|ui| {
                        ui.text_edit_singleline(&mut self.pack_output_folder);
                        if ui.button("Browse…").clicked() {
                            let start_dir = if self.pack_output_folder.trim().is_empty() {
                                "."
                            } else {
                                self.pack_output_folder.trim()
                            };
                            if let Some(path) =
                                FileDialog::new().set_directory(start_dir).pick_folder()
                            {
                                self.pack_output_folder =
                                    path.display().to_string();
                            }
                        }
                    });
                
                    ui.label("Output name components:");
                    ui.horizontal(|ui| {
                        ui.label("Name (e–z, lowercase):");
                        ui.text_edit_singleline(&mut self.pack_output_name);
                    });
                    ui.horizontal(|ui| {
                        ui.label("Number (0–99999):");
                        ui.text_edit_singleline(&mut self.pack_output_number);
                    });
                
                    ui.label(
                        "Additional compressed extensions (e.g. .lua .ini), separated by space or comma:",
                    );
                    ui.text_edit_singleline(&mut self.pack_compress_ext);

                    ui.add_space(4.0);
                    ui.horizontal(|ui| {
                        ui.label("Salt for packing (from salt_keys.json):");
                        if self.pack_salt_keys.is_empty() {
                            ui.weak("No salts loaded; built-in default salt will be used.");
                        } else {
                            let selected_text = self
                                .pack_selected_salt_index
                                .and_then(|i| self.pack_salt_keys.get(i))
                                .cloned()
                                .unwrap_or_else(|| "<none>".to_string());

                            egui::ComboBox::from_id_source("pack_salt_combo")
                                .selected_text(selected_text)
                                .show_ui(ui, |ui| {
                                    for (idx, salt) in self.pack_salt_keys.iter().enumerate() {
                                        let is_selected =
                                            self.pack_selected_salt_index == Some(idx);
                                        if ui
                                            .selectable_label(is_selected, salt)
                                            .clicked()
                                        {
                                            self.pack_selected_salt_index = Some(idx);
                                        }
                                    }
                                });
                        }
                    });
                
                    if ui.button("Pack").clicked() {
                        self.run_pack();
                    }
                });

                ui.add_space(8.0);
                ui.separator();
                ui.horizontal_wrapped(|ui| {
                    ui.label("Status:");
                    ui.strong(&self.status_message);
                });
            });

        // Central panel dedicated to the list output so it can grow with the window.
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("List output");
            ui.add_space(4.0);

            // Use all remaining height for the scroll area so it resizes with the window.
            let scroll_height = ui.available_height().max(0.0);
            egui::ScrollArea::vertical()
                .id_source("list_output_scroll")
                .max_height(scroll_height)
                .show(ui, |ui| {
                    ui.code(&self.list_output);
                });
        });
    }
}

fn main() -> eframe::Result<()> {
    let native_options = NativeOptions::default();

    eframe::run_native(
        "Mabinogi Pack Utilities 2 - GUI",
        native_options,
        Box::new(|_cc| Box::new(MabiPackGuiApp::default())),
    )
}