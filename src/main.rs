use clap::{arg, Command};

mod common;
mod encryption;
mod extract;
mod list;
mod pack;
mod salt_discovery;

fn get_inputs(input: &str) -> Vec<String> {
    let path = std::path::Path::new(input);
    if path.is_dir() {
        let mut files = Vec::new();
        if let Ok(entries) = std::fs::read_dir(path) {
            for entry in entries.flatten() {
                if let Some(name) = entry.file_name().to_str() {
                    if name.to_ascii_lowercase().ends_with(".it") {
                        files.push(entry.path().to_string_lossy().into_owned());
                    }
                }
            }
        }
        files
    } else {
        vec![input.to_string()]
    }
}

fn main() {
    let args = Command::new("Mabinogi pack utilities 2")
        .version("v1.3.1")
        .author("regomne <fallingsunz@gmail.com>")
        .after_help("\
EXAMPLES:
  # Extract specific files matching a regex pattern from ALL packs in a directory:
  mabi-pack2.exe extract -i \"E:\\mabi\\package\" -o \"E:\\Extracted\" -f \"(?i)chick.*wav\"

  # List files inside a single pack, or all packs in a directory:
  mabi-pack2.exe list -i \"E:\\mabi\\package\\data_00000.it\"
  mabi-pack2.exe list -i \"E:\\mabi\\package\"

  # Pack a directory into a new .it pack:
  mabi-pack2.exe pack -i \"E:\\Custom_Mods\" -o \"custom_01.it\"

  # Pack a directory using a specific encryption salt:
  mabi-pack2.exe pack -i \"E:\\Custom_Mods\" -o \"custom_01.it\" -s \"CuAVPMZx:E96:(Rxdw\"
")
        .subcommand(
            Command::new("pack")
                .about("Create a .it pack")
                .arg(arg!(-i --input <FOLDER> "Set the input folder to pack"))
                .arg(arg!(-o --output <PACK_NAME> "Set the output .it file name"))
                .arg(arg!(-s --salt <SALT> "Specify custom salt for encryption (if not specified, default will be used)").required(false))
                .arg(arg!(-a --additional_data "DEPRECATED: Add original filename to package").hide(true))
                .arg(
                    arg!(-f --"compress-format" <EXTENSTION> ... "Add an extension to compress in .it (Default: txt xml dds pmg set raw)")
                        .required(false)
                        .number_of_values(1)
                )
        )
        .subcommand(
            Command::new("extract")
                .about("Extract a .it pack (or all .it packs in a folder)")
                .arg(arg!(-i --input <PACK_NAME> "Set the input pack name or folder to extract"))
                .arg(arg!(-o --output <FOLDER> "Set the output folder"))
                .arg(
                    arg!(-f --filter <FILTER> ... "Set a filter when extracting, in regexp, multiple occurrences mean OR")
                        .required(false)
                        .number_of_values(1)
                )
                .arg(arg!(-c --check_additional "DEPRECATED: check additional data of filename").hide(true)),
        )
        .subcommand(
            Command::new("list")
                .about("Output the file list of a .it pack (or all .it packs in a folder)")
                .arg(arg!(-i --input <PACK_NAME> "Set the input pack name or folder to list"))
                .arg(
                    arg!(-o --output <LIST_FILE_NAME> "Set the list file name, output to stdout if not set")
                        .required(false)
                )
                .arg(arg!(-c --check_additional "DEPRECATED: check additional data of filename").hide(true)),
        )
        .get_matches();

    let ret = match if let Some(matches) = args.subcommand_matches("list") {
        let input = matches.value_of("input").unwrap();
        if matches.is_present("check_additional") {
            println!("WARNING: --check_additional has been deprecated");
        }
        let inputs = get_inputs(input);
        let mut all_success = true;
        for file in &inputs {
            match salt_discovery::discover_salt_with_defaults(file, vec![]) {
                Ok(salt) => {
                    if inputs.len() > 1 {
                        println!("-- Listing {} (salt: {}) --", file, salt);
                    }
                    if let Err(e) = list::run_list(file, matches.value_of("output"), Some(&salt)) {
                        println!("Failed to list {}: {}", file, e);
                        all_success = false;
                    }
                }
                Err(e) => {
                    println!("Salt discovery failed for {}: {}", file, e);
                    all_success = false;
                }
            }
        }
        if inputs.is_empty() {
            println!("No .it files found in the specified input.");
        }
        if all_success { Ok(()) } else { Err(anyhow::Error::msg("One or more files failed to list")) }
    } else if let Some(matches) = args.subcommand_matches("extract") {
        let input = matches.value_of("input").unwrap();
        if matches.is_present("check_additional") {
            println!("WARNING: --check_additional has been deprecated");
        }
        let inputs = get_inputs(input);
        let mut all_success = true;
        for file in &inputs {
            match salt_discovery::discover_salt_with_defaults(file, vec![]) {
                Ok(salt) => {
                    if inputs.len() > 1 {
                        println!("-- Extracting {} (salt: {}) --", file, salt);
                    }
                    if let Err(e) = extract::run_extract_with_salt(
                        file,
                        matches.value_of("output").unwrap(),
                        matches
                            .values_of("filter")
                            .map(|e| e.collect())
                            .unwrap_or(vec![]),
                        Some(&salt),
                    ) {
                        println!("Failed to extract {}: {}", file, e);
                        all_success = false;
                    }
                }
                Err(e) => {
                    println!("Salt discovery failed for {}: {}", file, e);
                    all_success = false;
                }
            }
        }
        if inputs.is_empty() {
            println!("No .it files found in the specified input.");
        }
        if all_success { Ok(()) } else { Err(anyhow::Error::msg("One or more files failed to extract")) }
    } else if let Some(matches) = args.subcommand_matches("pack") {
        if matches.is_present("additional_data") {
            println!("WARNING: --additional_data has been deprecated");
        }
        let salt_opt = matches.value_of("salt").map(|s| s.to_string()).or_else(|| {
            salt_discovery::get_json_salts().into_iter().next()
        });

        if salt_opt.is_none() {
            Err(anyhow::Error::msg("No salt provided. A valid salt must be specified via -s or within 'salt_keys.json'."))
        } else {
            pack::run_pack_with_salt(
                matches.value_of("input").unwrap(),
                matches.value_of("output").unwrap(),
                matches
                    .values_of("compress-format")
                    .map(|e| e.collect())
                    .unwrap_or(vec![]),
                salt_opt.as_deref(),
            )
        }
    } else {
        println!("please select a subcommand (type --help to get details)");
        Ok(())
    } {
        Err(e) => {
            println!("Err: {:?}", e);
            1
        }
        _ => 0,
    };
    std::process::exit(ret);
}
