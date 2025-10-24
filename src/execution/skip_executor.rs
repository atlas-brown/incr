use anyhow::Error;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;

use crate::command::Command;
use crate::config::BASH_COMMAND;
use crate::ops::debug_log;

pub(crate) fn run(command: &Command) -> Error {
    debug_log!("[{}] Skipping command", command.name);
    let command_string = match command.join() {
        Ok(string) => string,
        Err(error) => return error,
    };
    ShellCommand::new(BASH_COMMAND)
        .args(["-c", &command_string])
        .exec()
        .into()
}
