use crate::common;
use anyhow::{Context, Error};
use serde::Deserialize;
use std::fs::File;
use std::io::BufReader;

/// JSON format for salt_keys.json
#[derive(Deserialize)]
struct SaltKeyConfig {
    #[serde(default)]
    salt_keys: Vec<String>,
}

/// Salts hard-coded in the tool as a fallback / compatibility list.
pub fn get_default_salts() -> Vec<String> {
    vec![]
}

/// Salts loaded from salt_keys.json, or empty vec if the file is missing/invalid.
pub fn get_json_salts() -> Vec<String> {
    match load_salt_keys_from_json() {
        Ok(v) => v,
        Err(e) => {
            println!("ERROR loading salts: {:?}", e);
            Vec::new()
        }
    }
}

/// Combined salts used for auto-discovery: built-in + JSON + custom.
fn build_salt_list_for_discovery(mut custom_salts: Vec<String>) -> Vec<String> {
    let mut all_salts = get_default_salts();
    if let Ok(mut json_salts) = load_salt_keys_from_json() {
        all_salts.append(&mut json_salts);
    }
    all_salts.append(&mut custom_salts);
    all_salts
}

/// Load salts from salt_keys.json (returns an error if missing/invalid).
fn load_salt_keys_from_json() -> Result<Vec<String>, Error> {
    let mut candidate_paths = vec![std::path::PathBuf::from("salt_keys.json")];
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            candidate_paths.push(parent.join("salt_keys.json"));
            
            // Cargo dev environment fallback (target/release/../..)
            if let Some(grandparent) = parent.parent().and_then(|p| p.parent()) {
                candidate_paths.push(grandparent.join("salt_keys.json"));
            }
        }
    }

    let mut found_path = None;
    for path in &candidate_paths {
        if path.exists() {
            found_path = Some(path.clone());
            break;
        }
    }
    
    let file_path = found_path.ok_or_else(|| {
        Error::msg(format!(
            "salt_keys.json not found in any of the following locations: {:?}",
            candidate_paths
        ))
    })?;

    let file = File::open(&file_path).context(format!("opening {:?} failed", file_path))?;
    let reader = BufReader::new(file);
    let cfg: SaltKeyConfig =
        serde_json::from_reader(reader).context("parsing salt_keys.json failed")?;
    Ok(cfg.salt_keys)
}

/// Attempts to decrypt and validate a .it file with a specific salt
/// Returns true if the salt is correct (header validates), false otherwise
pub fn try_salt(fname: &str, salt_to_try: &str) -> bool {
    let salt_option = Some(salt_to_try);

    match try_decrypt_with_salt(fname, salt_option) {
        Ok(_) => true,
        Err(_) => false,
    }
}

fn try_decrypt_with_salt(fname: &str, salt: Option<&str>) -> Result<(), Error> {
    let fp = File::open(fname)?;
    let mut rd = BufReader::new(fp);
    let final_file_name = common::get_final_file_name(fname)?;

    // First, try to decrypt and validate the header
    let header = common::read_header_with_salt(&final_file_name, &mut rd, salt)
        .context("reading header failed")?;

    common::validate_header(&header)?;

    // Ensure we are looking at a supported pack format
    if header.version != 2 {
        return Err(Error::msg(format!(
            "unsupported header version {}",
            header.version
        )));
    }

    // Then, try to decrypt and validate the entries table as well.
    // This makes accidental "false positive" salts much less likely,
    // since both the header and all entry checksums must be consistent.
    let entries =
        common::read_entries_with_salt(&final_file_name, &header, &mut rd, salt)
            .context("reading entries failed")?;

    common::validate_entries(&entries)?;

    Ok(())
}

 /// Discovers the correct salt for a .it file by trying multiple candidates
/// Returns the working salt if found, or an error if none work
pub fn discover_salt(fname: &str, salt_candidates: &[String]) -> Result<String, Error> {
    for salt in salt_candidates {
        if try_salt(fname, salt) {
            return Ok(salt.clone());
        }
    }

    Err(Error::msg(
        "No matching salt found. The file may be corrupted or use an unknown salt.",
    ))
}

/// Convenience function that tries default salts plus custom ones.
/// Uses built-in salts, salts from salt_keys.json (if available), and any additional custom salts.
pub fn discover_salt_with_defaults(fname: &str, custom_salts: Vec<String>) -> Result<String, Error> {
    let all_salts = build_salt_list_for_discovery(custom_salts);
    discover_salt(fname, &all_salts)
}

/// Salts exposed to the GUI packer for manual selection (only JSON salts).
pub fn get_salts_for_gui() -> Result<Vec<String>, String> {
    load_salt_keys_from_json().map_err(|e| format!("{:?}", e))
}
