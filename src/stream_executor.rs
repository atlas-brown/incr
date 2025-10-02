use anyhow::{Result, anyhow, ensure};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::thread;

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, Command};
use crate::config::{CACHE_DIRECTORY, DEBUG};
use crate::ops;

pub fn run(command: Command) -> Result<ExitCode> {
    let sandbox_directory = create_sandbox_directory(&command)?;
    let mut child = command::spawn_command(&command, &sandbox_directory)?;

    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn(move || command::capture_stream(child_stdout, io::stdout()));
    let stderr_thread = thread::spawn(move || command::capture_stream(child_stderr, io::stderr()));

    let stdin = {
        let child_stdin = child.stdin.take().unwrap();
        let process_stdin = io::stdin().lock();
        command::capture_stream(process_stdin, child_stdin)?
    };

    let cache = CacheCursor::new(&command, &stdin)?;
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

    let exit_code = match cached_data {
        Some(_) => {
            command::kill_child(&child)?;
            None
        }
        None => child.wait()?.code(),
    };
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;

    if let Some(cached_data) = cached_data {
        cache::remove_sandbox(&sandbox_directory)?;
        return output_cached_data(&cache, &cached_data, &stdout, &stderr);
    }

    unimplemented!()
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

    Ok(ExitCode::from(data.exit_code as u8))
}
