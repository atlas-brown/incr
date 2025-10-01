use anyhow::Result;
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

    let mut child = command::spawn_command(&command, &cache.get_sandbox_directory())?;
    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn(move || command::capture_stream(child_stdout, io::stdout()));
    let stderr_thread = thread::spawn(move || command::capture_stream(child_stderr, io::stderr()));

    {
        let mut child_stdin = child.stdin.take().unwrap();
        child_stdin.write_all(&stdin)?;
        child_stdin.flush()?;
    }

    let exit_status = child.wait()?;
    let x = stdout_thread.join();
    let y = stderr_thread.join();
    println!("exit_status: {exit_status:?}");
    println!("{x:?} {y:?}");

    Ok(ExitCode::SUCCESS)
}
