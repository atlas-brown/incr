use anyhow::Result;
use rand::Rng;
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read};
use std::os::fd::AsRawFd;
use std::process::{Child, ChildStdin};
use std::sync::mpsc;
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::CacheData;
use crate::cache::batch_cache::{self, CacheCursor};
use crate::command::{self, ChildContext, Command, Runtime, RuntimeType};
use crate::config::{BUFFER_SIZE, Config, TraceType};
use crate::execution;
use crate::execution::dependency;
use crate::execution::run::{self, OutputMetadata, OutputResult, StdinResult};
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Debug)]
struct StdinContext {
    hash: u64,
    broken_pipe: bool,
    thread: Option<JoinHandle<Result<StdinResult>>>,
}

#[derive(Clone, Debug)]
enum CacheStatus {
    Valid(CacheData),
    Invalid(ExitCode),
}

pub(crate) fn execute(config: &Config, command: &Command) -> Result<ExitCode> {
    let mut runtime = create_child_runtime(config)?;
    if config.observe_command.is_some() && !matches!(runtime.typ, RuntimeType::Nothing) {
        runtime.effect_gate = Some(Arc::new(crate::effect_gate::EffectGate::create(
            runtime.stdout_file.with_extension("gate"),
        )?));
    }
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn(config, command, &runtime)?;

    let child_stdin = child.stdin.take().unwrap();
    let stdin_context = capture_stdin(child_stdin, &mut child)?;
    let cache = CacheCursor::from_hash(config, command, stdin_context.hash)?;
    cache.create_directory()?;

    if stdin_context.broken_pipe {
        let exit_code = child.wait()?.code().unwrap_or(1);
        run::join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)?;
        run::clean_child_runtime(&runtime)?;
        cache.clean()?;
        return Ok(ExitCode(exit_code));
    }

    let cache_status = load_cache_data(&cache, child, &runtime)?;
    let outputs = match run::join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)? {
        Some(outputs) => outputs,
        None => {
            run::clean_child_runtime(&runtime)?;
            return Ok(BROKEN_PIPE_CODE);
        }
    };

    match cache_status {
        CacheStatus::Valid(cached_data) => {
            debug_log!(
                "Cache valid: {} {:?} {}",
                command.name,
                command.arguments,
                stdin_context.hash,
            );
            output_cached_data(config, &cache, &cached_data, &outputs)
        }
        CacheStatus::Invalid(exit_code) => {
            debug_log!(
                "Cache invalid: {} {:?} {}",
                command.name,
                command.arguments,
                stdin_context.hash,
            );
            save_command_data(config, command, cache, &runtime, exit_code)
        }
    }
}

fn create_child_runtime(config: &Config) -> Result<Runtime> {
    let key = rand::rng().random_range(0..u64::MAX);
    let stdout_file = config.cache_directory.join(format!("stdout_{key}.incr"));
    let stderr_file = config.cache_directory.join(format!("stderr_{key}.incr"));

    if config.trace_type == TraceType::Nothing {
        return Ok(Runtime {
            typ: RuntimeType::Nothing,
            stdout_file,
            stderr_file,
            effect_gate: None,
        });
    }
    if config.trace_type == TraceType::TraceFile {
        let trace_file = if config.observe_command.is_some() {
            config.cache_directory.join(format!("observe_{key}.json"))
        } else {
            config.cache_directory.join(format!("trace_{key}.txt"))
        };
        return Ok(Runtime {
            typ: RuntimeType::TraceFile(trace_file),
            stdout_file,
            stderr_file,
            effect_gate: None,
        });
    }
    if config.trace_type == TraceType::Observe {
        let trace_file = config.cache_directory.join(format!("observe_{key}.json"));
        return Ok(Runtime {
            typ: RuntimeType::Observe(trace_file),
            stdout_file,
            stderr_file,
            effect_gate: None,
        });
    }

    let sandbox_directory = config.cache_directory.join(format!("sandbox_{key}"));
    if sandbox_directory.is_dir() {
        batch_cache::remove_sandbox(&sandbox_directory)?;
    } else if sandbox_directory.is_file() {
        fs::remove_file(&sandbox_directory)?;
    }
    fs::create_dir_all(&sandbox_directory)?;

    Ok(Runtime {
        typ: RuntimeType::Sandbox(sandbox_directory),
        stdout_file,
        stderr_file,
        effect_gate: None,
    })
}

fn capture_stdin(child_stdin: ChildStdin, child: &mut Child) -> Result<StdinContext> {
    let mut process_stdin = io::stdin().lock();
    if process_stdin.is_terminal() {
        return Ok(StdinContext {
            hash: ops::data::hash_bytes(&[]),
            broken_pipe: false,
            thread: None,
        });
    }

    let (send_channel, receive_channel) = mpsc::channel::<Vec<_>>();
    let stdin_broken = Arc::new(AtomicBool::new(false));
    let stdin_thread = thread::spawn({
        let stdin_broken = Arc::clone(&stdin_broken);
        move || {
            let result = run::forward_stdin(receive_channel, child_stdin)?;
            if result == StdinResult::BrokenPipe {
                stdin_broken.store(true, Ordering::Release);
            }
            Ok(result)
        }
    });
    let mut chunk = [0; BUFFER_SIZE];
    let mut hasher = Xxh3::new();

    loop {
        if stdin_broken.load(Ordering::Acquire) {
            break;
        }
        // The producer may keep stdin open after the command has enough data.
        // Poll rather than blocking forever on the next read in that case.
        let mut pollfd = libc::pollfd {
            fd: process_stdin.as_raw_fd(),
            events: libc::POLLIN,
            revents: 0,
        };
        let ready = unsafe { libc::poll(&mut pollfd, 1, 20) };
        if ready < 0 {
            let error = io::Error::last_os_error();
            if error.kind() == ErrorKind::Interrupted {
                continue;
            }
            return Err(error.into());
        }
        if ready == 0 {
            if child.try_wait()?.is_some() {
                stdin_broken.store(true, Ordering::Release);
                break;
            }
            continue;
        }
        let count = match process_stdin.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        if send_channel.send(chunk[..count].to_vec()).is_err() {
            break;
        }
        hasher.update(&chunk[..count]);
    }
    let broken_pipe = stdin_broken.load(Ordering::Acquire);
    drop(send_channel);

    Ok(StdinContext {
        hash: hasher.digest(),
        broken_pipe,
        thread: Some(stdin_thread),
    })
}

fn load_cache_data(cache: &CacheCursor<'_>, mut child: Child, runtime: &Runtime) -> Result<CacheStatus> {
    let cached_data = match cache.load_data()? {
        Some(cached_data) => {
            if dependency::check_cache_valid(cache, &cached_data)?
                && runtime
                    .effect_gate
                    .as_ref()
                    .is_none_or(|gate| gate.claim_replay())
            {
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
            run::clean_child_runtime(runtime)?;
            Ok(CacheStatus::Valid(cached_data))
        }
        None => {
            let exit_code = child.wait()?.code().unwrap_or(1);
            cache.clean()?;
            Ok(CacheStatus::Invalid(ExitCode(exit_code)))
        }
    }
}

fn output_cached_data(
    config: &Config,
    cache: &CacheCursor<'_>,
    cached_data: &CacheData,
    outputs: &OutputMetadata,
) -> Result<ExitCode> {
    let stdout_file = cache.get_stdout_file();
    let stderr_file = cache.get_stderr_file();

    let stdout_completed = run::output_data(
        &stdout_file,
        outputs.stdout_length,
        cached_data.compressed_output,
        &mut io::stdout().lock(),
    )? == OutputResult::Completed;
    let stderr_completed = run::output_data(
        &stderr_file,
        outputs.stderr_length,
        cached_data.compressed_output,
        &mut io::stderr().lock(),
    )? == OutputResult::Completed;

    if config.short_circuit && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !cached_data.write_outputs.is_empty() {
        cache.commit_output()?;
    }

    Ok(ExitCode(cached_data.exit_code))
}

fn save_command_data(
    config: &Config,
    command: &Command,
    cache: CacheCursor<'_>,
    runtime: &Runtime,
    exit_code: ExitCode,
) -> Result<ExitCode> {
    let mut trace = execution::parse_trace(runtime)?;
    let mut read_dependencies = if config.observe_command.is_some() {
        trace
            .reads
            .iter()
            .map(|path| {
                (
                    path.clone(),
                    trace
                        .initial_dependencies
                        .get(path)
                        .cloned()
                        .unwrap_or(crate::cache::DependencyKey::Uncacheable),
                )
            })
            .collect()
    } else {
        dependency::get_read_dependencies(&trace.reads, &trace.writes)?
    };
    let mut write_set = trace.writes;
    match &runtime.typ {
        RuntimeType::Sandbox(directory) => {
            fs::rename(directory, cache.get_sandbox_directory())?;
            cache.extract_sandbox_output()?;
            if !write_set.is_empty() {
                cache.commit_output()?;
            }
        }
        RuntimeType::Observe(_) | RuntimeType::TraceFile(_) if config.observe_command.is_some() => {
            if trace.replay_barriers.is_empty()
                && let Err(error) = cache.capture_observe_output(&write_set)
            {
                // The live command succeeded; unsupported output metadata
                // prevents reuse, rather than changing its observable status.
                debug_log!("Cannot capture output for reuse: {error:#}");
                trace.replay_barriers.push("uncapturable-output".to_owned());
            }
            // Observe already executed on the live filesystem. Replaying here
            // duplicates effects and can overwrite another command's changes.
        }
        _ => {}
    }
    if config.observe_command.is_none() {
        dependency::filter_dependencies(&mut read_dependencies, &mut write_set)?;
    }

    let cache_data = CacheData {
        replay_barriers: trace.replay_barriers,
        exit_code: exit_code.0,
        read_dependencies,
        write_outputs: write_set,
        compressed_output: config.compress_output,
    };

    fs::rename(&runtime.stdout_file, cache.get_stdout_file())?;
    fs::rename(&runtime.stderr_file, cache.get_stderr_file())?;
    cache.save_data(&cache_data)?;
    dependency::save_introspection(config, command, &cache_data)?;

    Ok(exit_code)
}
