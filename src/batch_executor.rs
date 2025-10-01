use anyhow::Result;
use std::process::ExitCode;

use crate::command_io::Command;

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");
    Ok(ExitCode::SUCCESS)
}
