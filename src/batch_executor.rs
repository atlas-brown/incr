use anyhow::Result;
use std::io::{self, IsTerminal, Read};
use std::process::ExitCode;

use crate::cache::CacheCursor;
use crate::command_io::Command;

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");

    let mut stdin = Vec::new();
    let mut process_stdin = io::stdin();
    if !process_stdin.is_terminal() {
        process_stdin.read_to_end(&mut stdin)?;
    }

    let command_cache = CacheCursor::new(command.name.clone());
    command_cache.create_directory()?;
    let cache = command_cache.get_invocation(&command, &stdin)?;
    cache.create_directory()?;
    println!("{cache:?}");

    Ok(ExitCode::SUCCESS)
}
