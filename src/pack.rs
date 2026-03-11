use crate::common::{self, FileEntry};
use crate::encryption;
use anyhow::{Context, Error};
use byte_slice_cast::AsByteSlice;
use byteorder::{LittleEndian, WriteBytesExt};
use miniz_oxide::deflate::compress_to_vec_zlib;
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

fn get_rel_path(root_dir: &str, full_path: &str) -> Result<String, Error> {
    let rel_name = Path::new(full_path).strip_prefix(root_dir).expect(&format!(
        "strip path error, full:{}, root:{}",
        full_path, root_dir
    ));
    Ok(rel_name.to_string_lossy().into_owned())
}

fn need_compress(fname: &str, extra_ext_list: &[&str]) -> bool {
    [".txt", ".xml", ".dds", ".pmg", ".set", ".raw"]
        .iter()
        .chain(extra_ext_list.iter())
        .any(|ext| fname.ends_with(ext))
}

fn pack_file(
    root_dir: &str,
    rel_path: &str,
    need_compress: bool,
) -> Result<(FileEntry, Vec<u8>), Error> {
    let mut stm = vec![];
    let mut fp = File::open(Path::new(root_dir).join(rel_path))?;
    fp.read_to_end(&mut stm)?;
    let original_size = stm.len();
    let (raw_stm, flags) = if need_compress {
        (compress_to_vec_zlib(&stm, 5), 1)
    } else {
        (stm, 0)
    };
    Ok((
        FileEntry {
            name: rel_path.to_owned(),
            checksum: 0,
            flags,
            offset: 0,
            original_size: original_size as u32,
            raw_size: raw_stm.len() as u32,
            key: [0; 16],
        },
        raw_stm,
    ))
}

fn write_header<T>(file_cnt: u32, key: &[u8], wr: &mut T) -> Result<(), Error>
where
    T: Write,
{
    const IT_VERSION: u8 = 2;
    let checksum = file_cnt + IT_VERSION as u32;
    let mut enc_stm = encryption::Snow2Encoder::new(key, wr);
    enc_stm.write_u32::<LittleEndian>(checksum)?;
    enc_stm.write_u8(IT_VERSION)?;
    enc_stm.write_u32::<LittleEndian>(file_cnt)?;
    Ok(())
}

fn write_entries<T>(entries: &[FileEntry], key: &[u8], wr: &mut T) -> Result<(), Error>
where
    T: Write,
{
    let mut enc_stm = encryption::Snow2Encoder::new(key, wr);
    entries
        .iter()
        .map(|ent| -> Result<(), Error> {
            let u16_str: Vec<u16> = ent.name.chars().map(|c| c as u32 as u16).collect();
            enc_stm.write_u32::<LittleEndian>(u16_str.len() as u32)?;
            enc_stm.write_all(u16_str.as_byte_slice())?;
            enc_stm.write_u32::<LittleEndian>(ent.checksum)?;
            enc_stm.write_u32::<LittleEndian>(ent.flags)?;
            enc_stm.write_u32::<LittleEndian>(ent.offset)?;
            enc_stm.write_u32::<LittleEndian>(ent.original_size)?;
            enc_stm.write_u32::<LittleEndian>(ent.raw_size)?;
            enc_stm.write_all(&ent.key)?;
            Ok(())
        })
        .collect()
}

fn ceil_1024(v: u64) -> u64 {
    (v + 1023) & 0u64.wrapping_sub(1024)
}

fn pack_requirements_text() -> &'static str {
    "Packing requirements:\n  - Output filename must start with a letter after 'd' (for example: e, f, g, ...). Do not start with a, b, c, or d.\n  - Output filename must follow: <name>_<number>.it\n  - <number> must be 1 to 5 digits (0 to 99999).\n  - Input folder must contain a top-level folder that contains data/ inside it.\n    Example valid structure: test/data/sound/chick.wav\n    Example invalid structure: data/sound/chick.wav"
}

fn validate_output_name(output_fname: &str) -> Result<(), Error> {
    let final_name = common::get_final_file_name(output_fname)?;
    let lower = final_name.to_ascii_lowercase();

    if !lower.ends_with(".it") {
        return Err(Error::msg(format!(
            "Invalid output filename '{}'.\n{}",
            final_name,
            pack_requirements_text()
        )));
    }

    let stem = final_name.strip_suffix(".it").unwrap_or(&final_name);
    let underscore_idx = stem.rfind('_').ok_or_else(|| {
        Error::msg(format!(
            "Invalid output filename '{}'. Missing '_' separator before the number.\n{}",
            final_name,
            pack_requirements_text()
        ))
    })?;

    let name_part = &stem[..underscore_idx];
    let number_part = &stem[underscore_idx + 1..];

    if name_part.is_empty() || number_part.is_empty() {
        return Err(Error::msg(format!(
            "Invalid output filename '{}'.\n{}",
            final_name,
            pack_requirements_text()
        )));
    }

    let first = name_part.chars().next().unwrap().to_ascii_lowercase();
    if !('e'..='z').contains(&first) {
        return Err(Error::msg(format!(
            "Invalid output filename '{}'. The name must start with a letter after 'd'.\n{}",
            final_name,
            pack_requirements_text()
        )));
    }

    if number_part.len() > 5 || !number_part.chars().all(|c| c.is_ascii_digit()) {
        return Err(Error::msg(format!(
            "Invalid output filename '{}'. The numeric suffix must be 1 to 5 digits.\n{}",
            final_name,
            pack_requirements_text()
        )));
    }

    Ok(())
}

fn validate_input_structure(input_folder: &str) -> Result<(), Error> {
    let root = Path::new(input_folder);
    if !root.is_dir() {
        return Err(Error::msg(format!(
            "Input folder '{}' does not exist or is not a directory.\n{}",
            input_folder,
            pack_requirements_text()
        )));
    }

    let has_direct_data = root.join("data").is_dir();
    let top_level_dirs: Vec<PathBuf> = std::fs::read_dir(root)?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    let has_nested_data = top_level_dirs.iter().any(|dir| dir.join("data").is_dir());

    if has_direct_data || !has_nested_data {
        return Err(Error::msg(format!(
            "Invalid input folder structure '{}'. Expected a top-level folder containing data/.\n{}",
            input_folder,
            pack_requirements_text()
        )));
    }

    Ok(())
}

pub fn run_pack(
    input_folder: &str,
    output_fname: &str,
    compress_ext: Vec<&str>,
) -> Result<(), Error> {
    // Preserve existing CLI behavior by using the built-in default salt (None => KEY_SALT).
    run_pack_with_salt(input_folder, output_fname, compress_ext, None)
}

/// Variant of run_pack that allows specifying a custom salt.
/// If salt is None, the built-in default KEY_SALT is used (same as the CLI behavior).
pub fn run_pack_with_salt(
    input_folder: &str,
    output_fname: &str,
    compress_ext: Vec<&str>,
    salt: Option<&str>,
) -> Result<(), Error> {
    validate_output_name(output_fname)?;
    validate_input_structure(input_folder)?;

    let file_names: Vec<String> = WalkDir::new(input_folder)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| !e.file_type().is_dir())
        .map(|e| get_rel_path(input_folder, e.into_path().to_str().unwrap()))
        .collect::<Result<Vec<String>, Error>>()
        .context("traversing dir failed")?;

    let entries_size = file_names
        .iter()
        .map(|s| s.chars().count() * 2 + 40)
        .sum::<usize>();

    let final_file_name = common::get_final_file_name(output_fname)?;
    let header_off = encryption::gen_header_offset(&final_file_name);
    let entries_off = encryption::gen_entries_offset(&final_file_name);
    let header_key = encryption::gen_header_key_with_salt(&final_file_name, salt);
    let entries_key = encryption::gen_entries_key_with_salt(&final_file_name, salt);

    let fs = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open(output_fname)?;
    let mut stm = BufWriter::new(fs);

    let start_content_off = ceil_1024((header_off + entries_off + entries_size) as u64);
    let mut content_off = start_content_off;
    let mut entries = Vec::<FileEntry>::with_capacity(file_names.len());
    for name in file_names {
        let (mut ent, content) =
            pack_file(input_folder, &name, need_compress(&name, &compress_ext))
                .context(format!("packing {} failed", name))?;
        stm.seek(SeekFrom::Start(content_off))?;
        stm.write_all(&content)?;
        ent.offset = ((content_off - start_content_off) / 1024) as u32;
        ent.checksum = ent.offset + ent.raw_size + ent.original_size + ent.flags;
        content_off = ceil_1024(content_off + ent.raw_size as u64);
        entries.push(ent);
    }

    stm.seek(SeekFrom::Start((header_off + entries_off) as u64))?;
    write_entries(&entries, &entries_key, &mut stm).context("writing entries failed")?;

    stm.seek(SeekFrom::Start(header_off as u64))?;
    write_header(entries.len() as u32, &header_key, &mut stm).context("writing header failed")?;

    Ok(())
}
