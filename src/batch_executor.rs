use anyhow::{Result, anyhow};
use std::fs;
use std::io::{self, IsTerminal, Read};
use std::path::Path;
use std::process::{Child, Command as ShellCommand, ExitCode, Stdio};

use crate::cache::CacheCursor;
use crate::command_io::Command;
use crate::config::{STRACE_COMMAND, TRACE_FILE, TRY_COMMAND};

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");

    let mut stdin = Vec::new();
    let mut process_stdin = io::stdin();
    if !process_stdin.is_terminal() {
        process_stdin.read_to_end(&mut stdin)?;
    }

    let command_cache = CacheCursor::new(command.name.clone());
    command_cache.create_directory()?;
    let cache = command_cache.get_invocation(&command, &stdin)?;
    cache.create_directory()?;

    cache.clean()?;
    let process = spawn_command(&command, &cache.get_sandbox_directory())?;
    let result = process.wait_with_output();
    println!("{result:?}");

    Ok(ExitCode::SUCCESS)
}

fn spawn_command(command: &Command, sandbox_directory: &Path) -> Result<Child> {
    let mut command_parts = Vec::with_capacity(command.arguments.len() + 1);
    command_parts.push(command.name.as_str());
    command_parts.extend(command.arguments.iter().map(|a| a.as_str()));
    let command_string = shlex::try_join(command_parts)?;

    let arguments = &[
        "-D",
        sandbox_directory
            .to_str()
            .ok_or(anyhow!("Could not format sandbox directory"))?,
        STRACE_COMMAND,
        "-yf",
        "--seccomp-bpf",
        "--trace=fork,clone,%file",
        "-o",
        &format!("/tmp/{TRACE_FILE}"),
        "bash",
        "-c",
        &shlex::try_quote(&command_string)?,
    ];

    fs::create_dir_all(&sandbox_directory)?;
    ShellCommand::new(TRY_COMMAND)
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.into())
}
