use anyhow::{Result, anyhow};
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::process::{Child, ChildStdin};
use std::sync::mpsc;
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildEnv, ChildOutput, Command, EnvType};
use crate::config::{CHUNK_SIZE, Config, TraceType};
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
struct Outputs {
    stdout_length: usize,
    stderr_length: usize,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let child_env = create_child_environment(config, command)?;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &child_env)?;

    let stdin_context = forward_stdin(child.stdin.take().unwrap())?;
    if execution::skip_cache(command, stdin_context.length) {
        join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)?;
        let exit_code = child.wait()?.code().unwrap();
        clean_child_environment(&child_env)?;
        return Ok(ExitCode(exit_code));
    }

    let cache = CacheCursor::from_hash(config, command, stdin_context.hash)?;
    cache.create_directory()?;
    let cache_status = load_cache_data(&cache, child, &child_env)?;
    let outputs = match join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)? {
        Some(lengths) => lengths,
        None => return Ok(BROKEN_PIPE_CODE),
    };

    let exit_code = match cache_status {
        CacheStatus::Valid(cached_data) => {
            debug_log!(
                "Cache valid: {} {:?} {}",
                command.name,
                command.arguments,
                stdin_context.hash,
            );
            return output_cached_data(config, &cache, &cached_data, &outputs);
        }
        CacheStatus::Invalid(exit_code) => {
            debug_log!(
                "Cache invalid: {} {:?} {}",
                command.name,
                command.arguments,
                stdin_context.hash,
            );
            exit_code
        }
    };

    save_command_data(config, cache, &child_env, exit_code)
}

fn create_child_environment(config: &Config, command: &Command) -> Result<ChildEnv> {
    let stdout_file = config
        .cache_directory
        .join(format!("stdout_{}.incr", command.hash));
    let stderr_file = config
        .cache_directory
        .join(format!("stderr_{}.incr", command.hash));

    if config.trace_type == TraceType::Nothing {
        return Ok(ChildEnv {
            typ: EnvType::Nothing,
            stdout_file,
            stderr_file,
        });
    }
    if config.trace_type == TraceType::TraceFile {
        let trace_file = config.cache_directory.join(format!("trace_{}.txt", command.hash));
        return Ok(ChildEnv {
            typ: EnvType::TraceFile(trace_file),
            stdout_file,
            stderr_file,
        });
    }

    let sandbox_directory = config.cache_directory.join(format!("sandbox_{}", command.hash));
    if sandbox_directory.is_dir() {
        cache::remove_sandbox(&sandbox_directory)?;
    } else if sandbox_directory.is_file() {
        fs::remove_file(&sandbox_directory)?;
    }
    fs::create_dir_all(&sandbox_directory)?;

    Ok(ChildEnv {
        typ: EnvType::Sandbox(sandbox_directory),
        stdout_file,
        stderr_file,
    })
}

fn clean_child_environment(child_env: &ChildEnv) -> Result<()> {
    ops::ignore_not_found(fs::remove_file(&child_env.stdout_file))?;
    ops::ignore_not_found(fs::remove_file(&child_env.stderr_file))?;
    match &child_env.typ {
        EnvType::Sandbox(directory) => cache::remove_sandbox(directory)?,
        EnvType::TraceFile(file) => ops::ignore_not_found(fs::remove_file(file))?,
        EnvType::Nothing => (),
    }
    Ok(())
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
    let mut length = 0;
    loop {
        let count = match process_stdin.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        send_channel.send(chunk[..count].to_vec())?;
        hasher.update(&chunk[..count]);
        length += count;
    }

    Ok(StdinContext {
        hash: hasher.digest(),
        length,
        thread: Some(stdin_thread),
    })
}

fn load_cache_data(cache: &CacheCursor<'_>, mut child: Child, child_env: &ChildEnv) -> Result<CacheStatus> {
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
            clean_child_environment(child_env)?;
            Ok(CacheStatus::Valid(cached_data))
        }
        None => {
            let exit_code = child.wait()?.code().unwrap();
            cache.clean_sandbox_directory()?;
            cache.clean_data_files()?;
            Ok(CacheStatus::Invalid(ExitCode(exit_code)))
        }
    }
}

fn join_stream_threads(
    stdin_thread: Option<JoinHandle<Result<()>>>,
    stdout_thread: JoinHandle<Result<ChildOutput>>,
    stderr_thread: JoinHandle<Result<ChildOutput>>,
) -> Result<Option<Outputs>> {
    if let Some(stdin_thread) = stdin_thread {
        stdin_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    }
    let stdout_result = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr_result = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    match (stdout_result, stderr_result) {
        (ChildOutput::Completed(stdout_length), ChildOutput::Completed(stderr_length)) => Ok(Some(Outputs {
            stdout_length,
            stderr_length,
        })),
        (ChildOutput::BrokenPipe, _) | (_, ChildOutput::BrokenPipe) => Ok(None),
    }
}

fn output_cached_data(
    config: &Config,
    cache: &CacheCursor<'_>,
    cached_data: &CacheData,
    outputs: &Outputs,
) -> Result<ExitCode> {
    let stdout_file = cache.get_stdout_file();
    let stderr_file = cache.get_stderr_file();

    let stdout_completed = execution::output_data(
        &stdout_file,
        outputs.stdout_length,
        &mut io::stdout().lock(),
        cached_data.compressed_output,
    )?;
    let stderr_completed = execution::output_data(
        &stderr_file,
        outputs.stderr_length,
        &mut io::stderr().lock(),
        cached_data.compressed_output,
    )?;

    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !cached_data.write_outputs.is_empty() {
        cache.commit_output()?;
    }

    Ok(ExitCode(cached_data.exit_code))
}

fn save_command_data(
    config: &Config,
    cache: CacheCursor<'_>,
    child_env: &ChildEnv,
    exit_code: ExitCode,
) -> Result<ExitCode> {
    let (read_set, mut write_set) = execution::parse_trace(child_env)?;
    let mut read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    if let EnvType::Sandbox(directory) = &child_env.typ {
        fs::rename(directory, cache.get_sandbox_directory())?;
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
    }
    execution::filter_dependencies(&mut read_dependencies, &mut write_set)?;

    fs::rename(&child_env.stdout_file, cache.get_stdout_file())?;
    fs::rename(&child_env.stderr_file, cache.get_stderr_file())?;
    cache.save_data(&CacheData {
        compressed_output: config.compress,
        exit_code: exit_code.0,
        read_dependencies,
        write_outputs: write_set,
    })?;

    Ok(exit_code)
}
