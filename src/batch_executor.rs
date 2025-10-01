use anyhow::{Result, anyhow, ensure};
use std::collections::HashSet;
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, ExitCode, Stdio};
use std::thread;

use crate::cache::CacheCursor;
use crate::command::{self, Command};
use crate::config::TRACE_FILE;

const PARSE_TRACE_SCRIPT: &str = include_str!("parse_trace.py");

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

    // TODO: logic checking cache validity
    cache.clean()?;

    let sandbox_directory = cache.get_sandbox_directory();
    let mut child = command::spawn_command(&command, &sandbox_directory)?;
    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn(move || command::capture_stream(child_stdout, io::stdout()));
    let stderr_thread = thread::spawn(move || command::capture_stream(child_stderr, io::stderr()));

    {
        let mut child_stdin = child.stdin.take().unwrap();
        child_stdin.write_all(&stdin)?;
        child_stdin.flush()?;
    }

    let exit_code = child.wait()?.code().unwrap();
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    println!("exit code: {exit_code:?}");
    println!("stdout: {stdout:?} stderr: {stderr:?}");

    let (read_set, write_set) = parse_command_trace(&sandbox_directory)?;
    println!("read: {read_set:?}");
    println!("write: {write_set:?}");

    Ok(ExitCode::SUCCESS)
}

fn parse_command_trace(sandbox_directory: &Path) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    let trace_file = sandbox_directory
        .join("upperdir")
        .join("tmp")
        .join(TRACE_FILE);
    let output = ShellCommand::new("python3")
        .args(&[
            "-c",
            PARSE_TRACE_SCRIPT,
            trace_file
                .to_str()
                .ok_or(anyhow!("Could not format trace file path"))?,
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?
        .wait_with_output()?;

    let mut read_set = HashSet::new();
    let mut write_set = HashSet::new();
    let mut parse_state = 0;
    for line in String::from_utf8(output.stdout)?.lines() {
        if parse_state == 0 {
            ensure!(line == "<read_set>");
            parse_state = 1;
        } else if parse_state == 1 {
            if line == "<write_set>" {
                parse_state = 2;
                continue;
            }
            read_set.insert(PathBuf::from(line));
        } else if parse_state == 2 {
            write_set.insert(PathBuf::from(line));
        }
    }
    ensure!(parse_state == 2);

    Ok((read_set, write_set))
}
