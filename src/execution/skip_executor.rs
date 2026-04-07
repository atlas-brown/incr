use anyhow::Error;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;

use crate::command::Command;
use crate::config::BASH_COMMAND;
use crate::ops::debug_log;

/// Bypasses incr entirely by exec-ing the command through `bash -c`. Used for shell builtins
/// and other commands in the ignore list that should not be traced or cached.
pub(crate) fn execute(command: &Command) -> Error {
    debug_log!("Skipping command: {} {:?}", command.name, command.arguments);
    let command_string = match command.join_string() {
        Ok(string) => string,
        Err(error) => return error,
    };
    ShellCommand::new(BASH_COMMAND)
        .args(["-c", &command_string])
        .exec()
        .into()
}
