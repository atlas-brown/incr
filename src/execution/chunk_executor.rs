use anyhow::Result;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;

use crate::command::Command;
use crate::config::{CHUNK_SIZE, CHUNK_WORKERS, Config};
use crate::ops::{ExitCode, debug_log};

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    todo!()
}
