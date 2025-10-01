use anyhow::{Result, anyhow};
use std::fs;
use std::io::{self, Error as IoError, ErrorKind, IsTerminal, Read};
use std::path::Path;
use std::process::{Child, Command as ShellCommand, ExitCode, Stdio};

use crate::cache::CacheCursor;
use crate::command_io::Command;
use crate::config::{
    COMMIT_DIRECTORY, DATA_FILE, OUTPUT_DIRECTORY, SANDBOX_DIRECTORY, STRACE_COMMAND, SUDO_SANDBOX,
    TRACE_FILE, TRY_COMMAND,
};

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
    let directory = cache.get_directory();
    cache.create_directory()?;

    clean_cache(directory)?;
    let sandbox_directory = directory.join(SANDBOX_DIRECTORY);
    let process = spawn_command(&command, &sandbox_directory)?;
    let result = process.wait_with_output();
    println!("{result:?}");

    Ok(ExitCode::SUCCESS)
}

fn clean_cache(directory: &Path) -> Result<()> {
    let sandbox_directory = directory.join(SANDBOX_DIRECTORY);
    if SUDO_SANDBOX {
        ShellCommand::new("sudo")
            .args(&[
                "rm",
                "-rf",
                sandbox_directory
                    .to_str()
                    .ok_or(anyhow!("Could not format sandbox directory"))?,
            ])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?;
    } else {
        ignore_not_found(fs::remove_dir_all(&sandbox_directory))?;
    }

    ignore_not_found(fs::remove_dir_all(&directory.join(OUTPUT_DIRECTORY)))?;
    ignore_not_found(fs::remove_dir_all(&directory.join(COMMIT_DIRECTORY)))?;
    ignore_not_found(fs::remove_file(&directory.join(DATA_FILE)))?;

    Ok(())
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

fn ignore_not_found(result: Result<(), IoError>) -> Result<()> {
    match result {
        Ok(()) => Ok(()),
        Err(error) => match error.kind() {
            ErrorKind::NotFound => Ok(()),
            _ => Err(error.into()),
        },
    }
}
