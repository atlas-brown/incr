use anyhow::{Result, anyhow, ensure};
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::path::Path;
use std::process::{Child, ChildStdin};
use std::sync::mpsc;
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildEnv, Command, Output};
use crate::config::{CHUNK_SIZE, Config, DEBUG, TraceType};
use crate::execution;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Debug)]
struct StdinContext {
    hash: u64,
    length: usize,
    thread: Option<JoinHandle<Result<()>>>,
}

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
    debug_log!(
        "[{}] Starting stream command (trace_type={})",
        command.name,
        config.trace_type,
    );

    let child_env = create_child_environment(config, command)?;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &child_env)?;
    debug_log!("[{}] Spawned stream child", command.name);

    let stdin_context = forward_stdin(child.stdin.take().unwrap())?;
    let cache = CacheCursor::from_hash(command, stdin_context.hash)?;
    cache.create_directory()?;
    debug_log!("[{}] Loaded cache directory", command.name);

    let cache_status = load_cache_data(&cache, child, &child_env, stdin_context.thread)?;
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (stdout, stderr) = match (stdout, stderr) {
        (Output::Completed(stdout), Output::Completed(stderr)) => (stdout, stderr),
        (Output::BrokenPipe, _) | (_, Output::BrokenPipe) => return Ok(BROKEN_PIPE_CODE),
    };
    debug_log!("[{}] Loaded cache data and child outputs", command.name);

    let exit_code = match cache_status {
        CacheStatus::Valid(cached_data) => {
            return output_cached_data(CacheContext {
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

    let (read_set, write_set) = execution::parse_trace(&child_env)?;
    let read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    if let ChildEnv::Sandbox(directory) = child_env {
        fs::rename(directory, cache.get_sandbox_directory())?;
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
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

fn create_child_environment(config: &Config, command: &Command) -> Result<ChildEnv> {
    if config.trace_type == TraceType::Nothing {
        panic!();
    }

    let hash = ops::hash_bytes(&ops::encode_to_vec(command)?);
    if config.trace_type == TraceType::TraceFile {
        let trace_file = Path::new(&command.cache_directory).join(format!("trace_{hash}.txt"));
        return Ok(ChildEnv::TraceFile(trace_file));
    }

    let sandbox_directory = Path::new(&command.cache_directory).join(format!("sandbox_{hash}"));
    if sandbox_directory.is_dir() {
        cache::remove_sandbox(&sandbox_directory)?;
    } else if sandbox_directory.is_file() {
        fs::remove_file(&sandbox_directory)?;
    }
    fs::create_dir_all(&sandbox_directory)?;

    Ok(ChildEnv::Sandbox(sandbox_directory))
}

fn forward_stdin(mut child_stdin: ChildStdin) -> Result<StdinContext> {
    let mut process_stdin = io::stdin().lock();
    if process_stdin.is_terminal() {
        return Ok(StdinContext {
            hash: ops::hash_bytes(&[]),
            length: 0,
            thread: None,
        });
    }

    let (send_channel, receive_channel) = mpsc::channel::<Vec<_>>();
    let stdin_thread = thread::spawn(move || {
        let mut broken = false;
        for chunk in receive_channel {
            if broken {
                continue;
            }
            if let Err(error) = child_stdin.write_all(&chunk) {
                if error.kind() != ErrorKind::BrokenPipe {
                    return Err(error.into());
                }
                broken = true;
            };
        }
        Ok(())
    });

    let mut chunk = [0; CHUNK_SIZE];
    let mut hasher = Xxh3::new();
    loop {
        let count = match process_stdin.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        send_channel.send(chunk[..count].to_vec())?;
        hasher.update(&chunk[..count]);
    }

    Ok(StdinContext {
        hash: hasher.digest(),
        length: 0,
        thread: Some(stdin_thread),
    })
}

fn load_cache_data(
    cache: &CacheCursor<'_>,
    mut child: Child,
    child_env: &ChildEnv,
    stdin_thread: Option<JoinHandle<Result<()>>>,
) -> Result<CacheStatus> {
    let cached_data = match cache.load_data()? {
        Some(cached_data) => {
            if execution::check_cache_valid(cache, &cached_data)? {
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
            match child_env {
                ChildEnv::Sandbox(directory) => cache::remove_sandbox(directory)?,
                ChildEnv::TraceFile(file) => ops::ignore_not_found(fs::remove_file(file))?,
            }
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

fn output_cached_data(context: CacheContext<'_>) -> Result<ExitCode> {
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
        ensure!(completed_stderr.as_slice() == &cached_data.stderr[..completed_stderr.len()]);
    }

    let remaining_stdout = &cached_data.stdout[completed_stdout.len()..];
    let remaining_stderr = &cached_data.stderr[completed_stderr.len()..];
    let stdout_completed = ops::output_data(remaining_stdout, io::stdout().lock())?;
    let stderr_completed = ops::output_data(remaining_stderr, io::stderr().lock())?;

    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !cached_data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Outputted cached data and committed files", command.name);

    Ok(ExitCode(cached_data.exit_code))
}
