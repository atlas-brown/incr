mod rules;

use crate::annotation::rules::{IGNORE_COMMANDS, PURE_COMMANDS, READ_ONLY_COMMANDS, STATELESS_COMMANDS};
use crate::command::Command;

pub(crate) fn check_ignorable(command: &Command) -> bool {
    IGNORE_COMMANDS.contains(&command.name.as_str())
}

pub(crate) fn check_pure(command: &Command) -> bool {
    todo!()
}

pub(crate) fn check_stateless(command: &Command) -> bool {
    todo!()
}

pub(crate) fn check_read_only(command: &Command) -> bool {
    todo!()
}
