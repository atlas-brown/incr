use anyhow::{Result, anyhow, ensure};
use nix::unistd::Pid;
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::path::Path;
use std::process::{Child, ChildStdin};
use std::sync::mpsc;
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::{self, CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildEnv, ChildOutput, Command, EnvType};
use crate::config::{CHUNK_SIZE, Config, DEBUG, TraceType};
use crate::execution;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};
use crate::scripts::{self, PreWrite};

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
    output_lengths: (usize, usize),
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    debug_log!(
        "[{}] Starting stream command (trace_type={})",
        command.name,
        config.trace_type,
    );

    let child_env = create_child_environment(config, command)?;
    let (sender, receiver) = std::sync::mpsc::channel();
    let trace_thread = thread::spawn({
        let config = config.clone();
        let command = command.clone();
        let child_env = child_env.clone();
        move || {
            let context = command::spawn_command(&config, &command, &child_env)?;
            let child_id = context.child.id();
            sender.send(context)?;
            scripts::run_tracer(Pid::from_raw(child_id as i32))
        }
    });
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = receiver.recv()?;

    let stdin_context = forward_stdin(child.stdin.take().unwrap())?;
    if execution::skip_cache(command, stdin_context.length) {
        join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)?;
        let exit_code = child.wait()?.code().unwrap();
        clean_child_environment(&child_env)?;
        debug_log!("[{}] Skipped caching", command.name);
        return Ok(ExitCode(exit_code));
    }

    let cache = CacheCursor::from_hash(command, stdin_context.hash)?;
    cache.create_directory()?;
    debug_log!("[{}] Loaded cache directory", command.name);

    let cache_status = load_cache_data(&cache, child, &child_env)?;
    let output_lengths = match join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)? {
        Some(lengths) => lengths,
        None => return Ok(BROKEN_PIPE_CODE),
    };
    debug_log!("[{}] Loaded cache data and saved outputs", command.name);

    let result = trace_thread.join().map_err(|e| anyhow!("{e:?}"))??;

    let exit_code = match cache_status {
        CacheStatus::Valid(cached_data) => {
            return output_cached_data(CacheContext {
                config,
                command,
                cache,
                cached_data,
                output_lengths,
            });
        }
        CacheStatus::Invalid(exit_code) => exit_code,
    };

    save_command_data(command, cache, &child_env, exit_code, result.0, result.1)
}

fn create_child_environment(config: &Config, command: &Command) -> Result<ChildEnv> {
    let hash = ops::hash_bytes(&ops::encode_to_vec(command)?);
    let cache_directory = Path::new(&command.cache_directory);
    let stdout_file = cache_directory.join(format!("stdout_{hash}.incr"));
    let stderr_file = cache_directory.join(format!("stderr_{hash}.incr"));

    if config.trace_type == TraceType::Nothing || true {
        return Ok(ChildEnv {
            typ: EnvType::Nothing,
            stdout_file,
            stderr_file,
        });
    }
    if config.trace_type == TraceType::TraceFile {
        let trace_file = cache_directory.join(format!("trace_{hash}.txt"));
        return Ok(ChildEnv {
            typ: EnvType::TraceFile(trace_file),
            stdout_file,
            stderr_file,
        });
    }

    let sandbox_directory = cache_directory.join(format!("sandbox_{hash}"));
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
                //child.wait()?;
            }
            clean_child_environment(child_env)?;
            Ok(CacheStatus::Valid(cached_data))
        }
        None => {
            let exit_code = 0;
            //let exit_code = child.wait()?.code().unwrap();
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
) -> Result<Option<(usize, usize)>> {
    if let Some(stdin_thread) = stdin_thread {
        stdin_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    }
    let stdout_result = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr_result = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    match (stdout_result, stderr_result) {
        (ChildOutput::Completed(stdout_length), ChildOutput::Completed(stderr_length)) => {
            Ok(Some((stdout_length, stderr_length)))
        }
        (ChildOutput::BrokenPipe, _) | (_, ChildOutput::BrokenPipe) => Ok(None),
    }
}

fn output_cached_data(context: CacheContext<'_>) -> Result<ExitCode> {
    let CacheContext {
        config,
        command,
        cache,
        cached_data,
        output_lengths,
    } = context;

    let (completed_stdout, completed_stderr) = output_lengths;
    let stdout_file = cache.get_stdout_file();
    let stderr_file = cache.get_stderr_file();

    if DEBUG {
        let stdout_length = fs::metadata(&stdout_file)?.len() as usize;
        let stderr_length = fs::metadata(&stderr_file)?.len() as usize;
        ensure!(completed_stdout <= stdout_length);
        ensure!(completed_stderr <= stderr_length);
    }

    let stdout_completed = execution::output_data(&stdout_file, completed_stdout, &mut io::stdout().lock())?;
    let stderr_completed = execution::output_data(&stderr_file, completed_stderr, &mut io::stderr().lock())?;
    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !cached_data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Outputted cached data and committed files", command.name);

    Ok(ExitCode(cached_data.exit_code))
}

fn save_command_data(
    command: &Command,
    cache: CacheCursor<'_>,
    child_env: &ChildEnv,
    exit_code: ExitCode,
    read_set: std::collections::HashSet<String>,
    write_set: std::collections::HashMap<String, PreWrite>,
) -> Result<ExitCode> {
    let read_dependencies = execution::get_read_dependencies_2(read_set, &write_set)?;
    let write_set = write_set
        .into_iter()
        .map(|(k, v)| std::path::PathBuf::from(k))
        .collect::<std::collections::HashSet<_>>();

    if let EnvType::Sandbox(directory) = &child_env.typ {
        fs::rename(directory, cache.get_sandbox_directory())?;
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
    }
    debug_log!("[{}] Extracted dependencies and committed files", command.name);

    fs::rename(&child_env.stdout_file, cache.get_stdout_file())?;
    fs::rename(&child_env.stderr_file, cache.get_stderr_file())?;
    cache.save_data(&CacheData {
        exit_code: exit_code.0,
        read_dependencies,
        write_outputs: write_set,
    })?;
    debug_log!("[{}] Saved command data", command.name);

    Ok(exit_code)
}
