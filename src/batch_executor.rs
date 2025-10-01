use anyhow::{Result, anyhow};
use std::io::{self, IsTerminal, Read, Write};
use std::process::ExitCode;
use std::thread;

use crate::cache::CacheCursor;
use crate::command::{self, Command};

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

    let (read_set, write_set) = command::parse_trace(&sandbox_directory)?;
    println!("read: {read_set:?}");
    println!("write: {write_set:?}");

    Ok(ExitCode::SUCCESS)
}
