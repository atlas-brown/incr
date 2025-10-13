use anyhow::Error;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;

use crate::command::Command;
use crate::ops::debug_log;

pub(crate) fn run(command: &Command) -> Error {
    debug_log!("[{}] Skipping command", command.name);
    ShellCommand::new(&command.name)
        .args(&command.arguments)
        .exec()
        .into()
}
