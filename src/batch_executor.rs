use anyhow::Result;
use std::io::{self, IsTerminal, Read};
use std::process::ExitCode;

use crate::cache::CacheCursor;
use crate::command_io::Command;

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");

    let cache = CacheCursor::new(command.name.clone());
    cache.create_directory()?;
    let mut stdin = Vec::new();
    let mut process_stdin = io::stdin();
    if !process_stdin.is_terminal() {
        process_stdin.read_to_end(&mut stdin)?;
    }
    println!("got stdin: {stdin:?}");

    Ok(ExitCode::SUCCESS)
}
