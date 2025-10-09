use anyhow::{Result, anyhow, ensure};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin};
use std::sync::mpsc;
use std::thread::{self, JoinHandle};

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, ChildContext, Command, Output};
use crate::config::{CACHE_DIRECTORY, CHUNK_SIZE, Config, DEBUG};
use crate::execution;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};

type StdinThread = Option<JoinHandle<Result<()>>>;

#[derive(Clone, Debug)]
enum CacheStatus {
    Valid(CacheData),
    Invalid(ExitCode),
}

#[derive(Clone, Debug)]
struct CacheContext<'c> {
    config: &'c Config,
    command: &'c Command,
    cache: CacheCursor<'c>,
    cached_data: CacheData,
    completed_stdout: Vec<u8>,
    completed_stderr: Vec<u8>,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    debug_log!("[{}] Starting stream command", command.name);

    let sandbox_directory = create_sandbox_directory(command)?;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &sandbox_directory)?;
    debug_log!("[{}] Spawned stream child", command.name);

    let (stdin, stdin_thread) = forward_stdin(child.stdin.take().unwrap())?;
    let cache = CacheCursor::new(command, &stdin)?;
    cache.create_directory()?;
    debug_log!("[{}] Loaded cache directory", command.name);

    let cache_status = load_cache_data(&sandbox_directory, &cache, child, stdin_thread)?;
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (stdout, stderr) = match (stdout, stderr) {
        (Output::Completed(stdout), Output::Completed(stderr)) => (stdout, stderr),
        (Output::BrokenPipe, _) | (_, Output::BrokenPipe) => return Ok(BROKEN_PIPE_CODE),
    };
    debug_log!("[{}] Loaded cache data and child outputs", command.name);

    let exit_code = match cache_status {
        CacheStatus::Valid(cached_data) => {
            return output_cached_data(&CacheContext {
                config,
                command,
                cache,
                cached_data,
                completed_stdout: stdout,
                completed_stderr: stderr,
            });
        }
        CacheStatus::Invalid(exit_code) => exit_code,
    };

    let (read_set, write_set) = execution::parse_trace(&sandbox_directory)?;
    let read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    fs::rename(sandbox_directory, cache.get_sandbox_directory())?;
    cache.extract_sandbox_output()?;
    if !write_set.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Extracted dependencies and committed files", command.name);

    cache.save_data(&CacheData {
        exit_code: exit_code.0,
        stdout,
        stderr,
        read_dependencies,
        write_outputs: write_set,
    })?;

    Ok(exit_code)
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

fn forward_stdin(mut child_stdin: ChildStdin) -> Result<(Vec<u8>, StdinThread)> {
    let mut process_stdin = io::stdin().lock();
    if process_stdin.is_terminal() {
        return Ok((Vec::new(), None));
    }

    let (send_channel, receive_channel) = mpsc::channel::<Vec<_>>();
    let stdin_thread = thread::spawn(move || {
        for chunk in receive_channel {
            child_stdin.write_all(&chunk)?;
        }
        Ok(())
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

    Ok((stdin, Some(stdin_thread)))
}

fn load_cache_data(
    sandbox_directory: &Path,
    cache: &CacheCursor<'_>,
    mut child: Child,
    stdin_thread: StdinThread,
) -> Result<CacheStatus> {
    let cached_data = match cache.load_data()? {
        Some(cached_data) => {
            if execution::check_cache_valid(&cache, &cached_data)? {
                Some(cached_data)
            } else {
                None
            }
        }
        None => None,
    };

    match cached_data {
        Some(cached_data) => {
            if child.try_wait()?.is_none() {
                command::kill_child(&child)?;
                child.wait()?;
            }
            cache::remove_sandbox(sandbox_directory)?;
            Ok(CacheStatus::Valid(cached_data))
        }
        None => {
            if let Some(stdin_thread) = stdin_thread {
                stdin_thread.join().map_err(|e| anyhow!("{e:?}"))??;
            }
            let exit_code = child.wait()?.code().unwrap();
            cache.clean_sandbox_directory()?;
            cache.clean_data()?;
            Ok(CacheStatus::Invalid(ExitCode(exit_code)))
        }
    }
}

fn output_cached_data(context: &CacheContext<'_>) -> Result<ExitCode> {
    let CacheContext {
        config,
        command,
        cache,
        cached_data,
        completed_stdout,
        completed_stderr,
    } = context;

    ensure!(completed_stdout.len() <= cached_data.stdout.len());
    ensure!(completed_stderr.len() <= cached_data.stderr.len());
    if DEBUG {
        ensure!(completed_stdout.as_slice() == &cached_data.stdout[..completed_stdout.len()]);
        ensure!(completed_stderr.as_slice() == &cached_data.stderr[..completed_stdout.len()]);
    }

    let remaining_stdout = &cached_data.stdout[completed_stdout.len()..];
    let remaining_stderr = &cached_data.stderr[completed_stderr.len()..];
    let stdout_completed = ops::output_data(remaining_stdout, io::stdout().lock())?;
    let stderr_completed = ops::output_data(remaining_stderr, io::stderr().lock())?;

    if !config.complete_after_downstream_failure && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !cached_data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Outputted cached data and committed files", command.name);

    Ok(ExitCode(cached_data.exit_code))
}
