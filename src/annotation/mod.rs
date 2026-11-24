pub(crate) mod rules;

use std::collections::HashMap;

use crate::annotation::rules::IGNORE_COMMANDS;
use crate::command::Command;

pub(crate) fn skip_command(command: &Command, environment: &HashMap<String, String>) -> bool {
    IGNORE_COMMANDS.contains(&command.name.as_str())
        || environment.contains_key(&format!("BASH_FUNC_{}%%", command.name))
}

/// Standard tools that never use an inherited fd above 2 (configure's `exec 5>>config.log`).
// TODO: temporary allowlist; replace by having observe report reads/writes on inherited fds.
pub(crate) fn ignores_inherited_descriptors(command: &Command) -> bool {
    const TOOLS: &[&str] = &[
        "awk", "basename", "cat", "chmod", "cp", "cut", "dirname", "egrep", "expr", "fgrep",
        "gawk", "grep", "head", "ln", "mawk", "mkdir", "mv", "rm", "rmdir", "sed", "sort",
        "tail", "touch", "tr", "uname", "uniq", "wc",
    ];
    let tool = command.name.rsplit('/').next().unwrap_or_default();
    command.standard_tool
        && TOOLS.contains(&tool)
        && command.arguments.iter().all(|argument| {
            !argument.contains("/dev/fd")
                && !argument.contains("/proc/")
                && !argument.contains("/dev/std")
                && argument != "-f"
                && !argument.starts_with("--file")
                && !(argument.starts_with('-')
                    && !argument.starts_with("--")
                    && argument.contains('f')
                    && matches!(tool, "sed" | "awk" | "gawk" | "mawk" | "grep" | "egrep" | "fgrep"))
        })
}

pub(crate) fn check_pure(command: &Command) -> bool {
    if !command.standard_tool {
        return false;
    }
    match command.name.as_str() {
        "basename" => true,
        "uniq" => command
            .arguments
            .iter()
            .all(|argument| matches!(argument.as_str(), "-c" | "-d" | "-u" | "-i")),
        "rev" | "cat" => command.arguments.is_empty(),
        "tr" => command
            .arguments
            .iter()
            .all(|argument| !argument.starts_with("--")),
        _ => false,
    }
}

#[derive(Clone, Copy)]
pub(crate) enum ChunkMode {
    Bytes,
    Lines,
}

pub(crate) fn chunk_mode(command: &Command, assume_text: bool) -> Option<ChunkMode> {
    if !command.standard_tool {
        return None;
    }
    match command.name.as_str() {
        "cat" if command.arguments.is_empty() => Some(ChunkMode::Bytes),
        "tr" if command.arguments.len() == 2
            && command.arguments.iter().all(|argument| {
                !argument.is_empty() && argument.bytes().all(|byte| byte.is_ascii_alphanumeric())
            }) =>
        {
            Some(ChunkMode::Bytes)
        }
        "rev"
            if assume_text
                && command.arguments.is_empty()
                && matches!(
                    command.environment.get("LC_ALL").map(String::as_str),
                    Some("C" | "POSIX")
                ) =>
        {
            Some(ChunkMode::Lines)
        }
        _ => None,
    }
}

pub(crate) fn check_read_only(command: &Command) -> bool {
    if !command.standard_tool {
        return false;
    }
    match command.name.as_str() {
        "cat" | "comm" | "head" | "paste" | "tail" => true,
        "find" => !command.arguments.iter().any(|argument| {
            matches!(
                argument.as_str(),
                "-exec"
                    | "-execdir"
                    | "-ok"
                    | "-okdir"
                    | "-delete"
                    | "-fprint"
                    | "-fprint0"
                    | "-fprintf"
                    | "-fls"
            )
        }),
        _ => false,
    }
}
