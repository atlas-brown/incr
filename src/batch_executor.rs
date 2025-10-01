use anyhow::Result;
use std::process::ExitCode;

use crate::cache;
use crate::command_io::Command;

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");
    cache::create_command_directory(&command.name)?;
    Ok(ExitCode::SUCCESS)
}
