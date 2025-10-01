use anyhow::Result;
use std::process::ExitCode;

use crate::cache::CacheCursor;
use crate::command_io::Command;

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");
    let cache = CacheCursor::new(command);
    cache.create_directory()?;

    Ok(ExitCode::SUCCESS)
}
