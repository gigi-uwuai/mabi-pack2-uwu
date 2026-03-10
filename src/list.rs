use crate::common;
use anyhow::{Context, Error};
use std::fs::{File, OpenOptions};
use std::io::{self, BufReader, Write};

pub fn list_entries_for_file(fname: &str, salt: Option<&str>) -> Result<Vec<String>, Error> {
    let fp = File::open(fname)?;
    let mut rd = BufReader::new(fp);
    let final_file_name = common::get_final_file_name(fname)?;
    let header =
        common::read_header_with_salt(&final_file_name, &mut rd, salt).context("reading header failed")?;

    common::validate_header(&header)?;
    if header.version != 2 {
        return Err(Error::msg(format!(
            "header version {} not supported",
            header.version
        )));
    }

    let entries = common::read_entries_with_salt(&final_file_name, &header, &mut rd, salt)
        .context("reading entries failed")?;
    common::validate_entries(&entries)?;

    Ok(entries.into_iter().map(|e| e.name).collect())
}

pub fn run_list(fname: &str, output: Option<&str>, salt: Option<&str>) -> Result<(), Error> {
    let entries = list_entries_for_file(fname, salt)?;

    let output_stream: Result<Box<dyn Write>, Error> =
        output.map_or(Ok(Box::new(io::stdout())), |path| {
            OpenOptions::new()
                .create(true)
                .write(true)
                .append(true)
                .open(path)
                .map(|f| Box::new(f) as Box<dyn Write>)
                .map_err(Error::new)
        });
    let mut output_stream = output_stream?;

    entries.iter().for_each(|e| {
        writeln!(output_stream, "{}", e).unwrap();
    });
    Ok(())
}
