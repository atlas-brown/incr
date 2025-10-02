use anyhow::{Result, anyhow};
use std::io::{self, IsTerminal, Read, Write};
use std::process::ExitCode;
use std::thread;

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, Command};

pub fn run(command: Command) -> Result<ExitCode> {
    let mut stdin = Vec::new();
    {
        let mut process_stdin = io::stdin().lock();
        if !process_stdin.is_terminal() {
            process_stdin.read_to_end(&mut stdin)?;
        }
    }

    let cache = CacheCursor::new(&command, &stdin)?;
    cache.create_directory()?;
    if let Some(cached_data) = cache.load_data()?
        && command::check_read_dependencies(&cached_data.read_dependencies)?
    {
        return output_cached_data(&cache, &cached_data);
    }

    cache.remove_sandbox_directory()?;
    cache.remove_cache_data()?;
    let data = run_command(&command, &cache, &stdin)?;
    cache.save_data(&data)?;

    Ok(ExitCode::from(data.exit_code as u8))
}

fn run_command(command: &Command, cache: &CacheCursor<'_>, stdin: &[u8]) -> Result<CacheData> {
    let sandbox_directory = cache.get_sandbox_directory();
    let mut child = command::spawn_command(command, &sandbox_directory)?;

    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn(move || command::capture_stream(child_stdout, io::stdout()));
    let stderr_thread = thread::spawn(move || command::capture_stream(child_stderr, io::stderr()));

    {
        let mut child_stdin = child.stdin.take().unwrap();
        child_stdin.write_all(stdin)?;
        child_stdin.flush()?;
    }

    let exit_code = child.wait()?.code().unwrap();
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (read_set, write_set) = command::parse_trace(&sandbox_directory)?;

    let read_dependencies = command::get_read_dependencies(read_set, &write_set)?;
    cache.extract_sandbox_output()?;
    if !write_set.is_empty() {
        cache.commit_output()?;
    }

    Ok(CacheData {
        exit_code,
        stdout,
        stderr,
        read_dependencies,
        write_outputs: write_set,
    })
}

fn output_cached_data(cache: &CacheCursor<'_>, data: &CacheData) -> Result<ExitCode> {
    {
        let mut process_stdout = io::stdout().lock();
        process_stdout.write_all(&data.stdout)?;
        process_stdout.flush()?;
    }
    {
        let mut process_stderr = io::stderr().lock();
        process_stderr.write_all(&data.stderr)?;
        process_stderr.flush()?;
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    Ok(ExitCode::from(data.exit_code as u8))
}
