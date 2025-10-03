use anyhow::{Result, anyhow, ensure};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::ChildStdin;
use std::sync::mpsc;
use std::thread;

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, ChildContext, Command, Output};
use crate::config::{CACHE_DIRECTORY, CHUNK_SIZE, Config, DEBUG};
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode};

pub fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let sandbox_directory = create_sandbox_directory(command)?;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &sandbox_directory)?;

    let stdin = forward_stdin(child.stdin.take().unwrap())?;
    let cache = CacheCursor::new(command, &stdin)?;
    cache.create_directory()?;
    let cached_data = match cache.load_data()? {
        Some(cached_data) => {
            if command::check_read_dependencies(&cached_data.read_dependencies)? {
                Some(cached_data)
            } else {
                None
            }
        }
        None => None,
    };

    let exit_code = if cached_data.is_some() {
        if child.try_wait()?.is_none() {
            command::kill_child(&child)?;
            child.wait()?;
        }
        cache::remove_sandbox(&sandbox_directory)?;
        None
    } else {
        let exit_code = child.wait()?.code();
        cache.clean_data()?;
        exit_code
    };

    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (stdout, stderr) = match (stdout, stderr) {
        (Output::Completed(stdout), Output::Completed(stderr)) => (stdout, stderr),
        _ => return Ok(BROKEN_PIPE_CODE),
    };

    if let Some(cached_data) = cached_data {
        ensure!(exit_code.is_none());
        return output_cached_data(&cache, &cached_data, &stdout, &stderr);
    }
    let exit_code = exit_code.unwrap();

    let (read_set, write_set) = command::parse_trace(&sandbox_directory)?;
    let read_dependencies = command::get_read_dependencies(read_set, &write_set)?;
    fs::rename(sandbox_directory, cache.get_sandbox_directory())?;
    cache.extract_sandbox_output()?;
    if !write_set.is_empty() {
        cache.commit_output()?;
    }

    cache.save_data(&CacheData {
        exit_code,
        stdout,
        stderr,
        read_dependencies,
        write_outputs: write_set,
    })?;

    Ok(ExitCode(exit_code))
}

fn create_sandbox_directory(command: &Command) -> Result<PathBuf> {
    let mut hasher = Sha256::new();
    hasher.update(ops::encode_to_vec(command)?);
    let directory_name = format!("sandbox_{:x}", hasher.finalize());
    let directory = Path::new(CACHE_DIRECTORY).join(directory_name);

    if directory.is_dir() {
        fs::remove_dir_all(&directory)?;
    } else if directory.is_file() {
        fs::remove_file(&directory)?;
    }
    fs::create_dir_all(&directory)?;

    Ok(directory)
}

fn forward_stdin(mut child_stdin: ChildStdin) -> Result<Vec<u8>> {
    let mut process_stdin = io::stdin().lock();
    if process_stdin.is_terminal() {
        return Ok(Vec::new());
    }

    let (send_channel, receive_channel) = mpsc::channel::<Vec<_>>();
    thread::spawn(move || {
        for chunk in receive_channel {
            if child_stdin.write_all(&chunk).is_err() {
                break;
            }
        }
    });

    let mut stdin = Vec::new();
    let mut chunk = [0; CHUNK_SIZE];
    loop {
        let count = match process_stdin.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        send_channel.send(chunk[..count].to_vec())?;
        stdin.extend_from_slice(&chunk[..count]);
    }

    Ok(stdin)
}

fn output_cached_data(
    cache: &CacheCursor<'_>,
    data: &CacheData,
    stdout: &[u8],
    stderr: &[u8],
) -> Result<ExitCode> {
    ensure!(stdout.len() <= data.stdout.len());
    ensure!(stderr.len() <= data.stderr.len());
    if DEBUG {
        ensure!(stdout == &data.stdout[..stdout.len()]);
        ensure!(stderr == &data.stderr[..stderr.len()]);
    }

    if stdout.len() < data.stdout.len() {
        let mut process_stdout = io::stdout().lock();
        process_stdout.write_all(&data.stdout[stdout.len()..])?;
        process_stdout.flush()?;
    }
    if stderr.len() < data.stderr.len() {
        let mut process_stderr = io::stderr().lock();
        process_stderr.write_all(&data.stderr[stderr.len()..])?;
        process_stderr.flush()?;
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }

    Ok(ExitCode(data.exit_code))
}
