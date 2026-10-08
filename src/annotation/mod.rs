pub(crate) mod rules;

use std::collections::{HashMap, HashSet};

use crate::annotation::rules::{
    Condition, IGNORE_COMMANDS, PURE_COMMANDS, READ_ONLY_COMMANDS, STATELESS_COMMANDS,
};
use crate::command::Command;

#[derive(Clone, Debug)]
struct CommandArguments {
    values: Vec<String>,
    flags: HashSet<String>,
}

pub(crate) fn skip_command(command: &Command, environment: &HashMap<String, String>) -> bool {
    IGNORE_COMMANDS.contains(&command.name.as_str())
        || environment.contains_key(&format!("BASH_FUNC_{}%%", command.name))
}

pub(crate) fn check_pure(command: &Command) -> bool {
    if !command.standard_tool {
        return false;
    }
    // File operands and output flags make otherwise stream-only commands impure.
    // Keep only forms whose complete argument grammar is known here.
    match command.name.as_str() {
        "basename" => check_conditions(PURE_COMMANDS, command),
        // sort may spill to TMPDIR even without file operands. It needs tracing.
        "sort" => false,
        "uniq" => command
            .arguments
            .iter()
            .all(|a| matches!(a.as_str(), "-c" | "-d" | "-u" | "-i")),
        "rev" => command.arguments.is_empty(),
        "tr" => command.arguments.iter().all(|a| !a.starts_with("--")),
        _ => false,
    }
}

pub(crate) fn check_stateless(command: &Command) -> bool {
    check_conditions(STATELESS_COMMANDS, command)
}

pub(crate) fn check_read_only(command: &Command) -> bool {
    if !command.standard_tool {
        return false;
    }
    match command.name.as_str() {
        // These languages can write files or launch arbitrary programs based
        // on stdin, so a prior read-only execution is not a proof of purity.
        "awk" | "sed" => false,
        "find" => !command.arguments.iter().any(|a| {
            matches!(
                a.as_str(),
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
        _ => check_conditions(READ_ONLY_COMMANDS, command),
    }
}

fn check_conditions(conditions: &[Condition], command: &Command) -> bool {
    if conditions.iter().all(|c| c.name != command.name) {
        return false;
    }
    let arguments = parse_arguments(&command.arguments);
    conditions
        .iter()
        .any(|c| check_condition(c, command, &arguments.values, &arguments.flags))
}

fn check_condition(
    condition: &Condition,
    command: &Command,
    values: &[String],
    flags: &HashSet<String>,
) -> bool {
    condition.name == command.name
        && condition.disallowed_flags.iter().all(|&f| !flags.contains(f))
        && values.len() <= condition.max_arguments
}

fn parse_arguments(arguments: &[String]) -> CommandArguments {
    let mut values = Vec::new();
    let mut flags = HashSet::new();

    for argument in arguments {
        if argument.starts_with("--") && argument.len() >= 3 {
            match argument.find("=") {
                Some(index) => flags.insert(argument[2..index].to_lowercase()),
                None => flags.insert(argument[2..].to_lowercase()),
            };
        } else if let Some(short) = argument.strip_prefix('-').filter(|s| !s.is_empty()) {
            // Iterate characters: byte slicing panics on non-ASCII arguments.
            let short = short.split_once('=').map_or(short, |(name, _)| name);
            for flag in short.chars() {
                flags.insert(flag.to_string());
            }
        } else {
            values.push(argument.clone());
        }
    }

    CommandArguments { values, flags }
}
