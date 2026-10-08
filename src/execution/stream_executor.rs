use anyhow::Result;
use rand::Rng;
use std::fs;
use std::io::{self, ErrorKind, IsTerminal, Read};
use std::os::fd::AsRawFd;
use std::process::{Child, ChildStdin};
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
use crate::execution::run;
use crate::ops::stream::TransferOutcome;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Debug)]
struct StdinContext {
    hash: u64,
    broken_pipe: bool,
    thread: Option<JoinHandle<Result<TransferOutcome>>>,
}

#[derive(Clone, Debug)]
enum CacheStatus {
    Valid(CacheData),
    Invalid(ExitCode),
}

pub(crate) fn execute(config: &Config, command: &Command) -> Result<ExitCode> {
    let candidates = crate::cache::candidates::validate(config, command)?;
    let mut runtime = create_child_runtime(config)?;
    if config.observe_command.is_some() && !matches!(runtime.kind, RuntimeType::Nothing) {
        runtime.effect_gate = Some(Arc::new(crate::effect_gate::EffectGate::create(
            runtime.stdout_file.with_extension("gate"),
        )?));
    }
    if !candidates.is_empty() && runtime.effect_gate.is_some() {
        runtime.snapshot_directory = Some(runtime.stdout_file.with_extension("snapshot"));
    }
    let _cleanup = run::TemporaryRuntime(&runtime);
    if let Some(directory) = &runtime.snapshot_directory {
        let mut excluded = candidates[0].data.write_outputs.clone();
        for candidate in &candidates[1..] {
            excluded.retain(|path| candidate.data.write_outputs.contains(path));
        }
        fs::create_dir_all(directory)?;
        fs::write(directory.join("exclude.json"), serde_json::to_vec(&excluded)?)?;
    }

    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn(config, command, &runtime)?;

    let child_stdin = child.stdin.take().unwrap();
    let stdin_context = capture_stdin(child_stdin, &mut child, &config.cache_directory)?;
    let selected = candidates
        .into_iter()
        .find(|candidate| candidate.stdin_hash == stdin_context.hash);
    let (cache, prevalidated) = match selected {
        Some(candidate) => (candidate.cache, Some(candidate.data)),
        None => (CacheCursor::from_hash(config, command, stdin_context.hash)?, None),
    };
    cache.create_directory()?;

    if stdin_context.broken_pipe {
        let exit_code = command::exit_code(child.wait()?);
        run::join_stream_threads(stdin_context.thread, stdout_thread, stderr_thread)?;
        run::clean_child_runtime(&runtime)?;
        cache.clean()?;
        return Ok(ExitCode(exit_code));
    }

    let cache_status = load_cache_data(config, &cache, child, &runtime, prevalidated)?;
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
            run::clean_child_runtime(&runtime)?;
            run::replay(config, &cache, &cached_data, &outputs)
        }
        CacheStatus::Invalid(exit_code) => {
            debug_log!(
                "Cache invalid: {} {:?} {}",
                command.name,
                command.arguments,
                stdin_context.hash,
            );
            let status = save_command_data(config, command, cache, &runtime, exit_code)?;
            Ok(if outputs.broken_pipe {
                BROKEN_PIPE_CODE
            } else {
                status
            })
        }
    }
}

fn create_child_runtime(config: &Config) -> Result<Runtime> {
    let key = rand::rng().random_range(0..u64::MAX);
    let stdout_file = config.cache_directory.join(format!("stdout_{key}.incr"));
    let stderr_file = config.cache_directory.join(format!("stderr_{key}.incr"));

    if config.trace_type == TraceType::Nothing {
        return Ok(Runtime {
            kind: RuntimeType::Nothing,
            stdout_file,
            stderr_file,
            effect_gate: None,
            snapshot_directory: None,
        });
    }
    if config.trace_type == TraceType::TraceFile {
        let trace_file = if config.observe_command.is_some() {
            config.cache_directory.join(format!("observe_{key}.json"))
        } else {
            config.cache_directory.join(format!("trace_{key}.txt"))
        };
        return Ok(Runtime {
            kind: RuntimeType::TraceFile(trace_file),
            stdout_file,
            stderr_file,
            effect_gate: None,
            snapshot_directory: None,
        });
    }
    if config.trace_type == TraceType::Observe {
        let trace_file = config.cache_directory.join(format!("observe_{key}.json"));
        return Ok(Runtime {
            kind: RuntimeType::Observe(trace_file),
            stdout_file,
            stderr_file,
            effect_gate: None,
            snapshot_directory: None,
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
        kind: RuntimeType::Sandbox(sandbox_directory),
        stdout_file,
        stderr_file,
        effect_gate: None,
        snapshot_directory: None,
    })
}

fn capture_stdin(
    child_stdin: ChildStdin,
    child: &mut Child,
    directory: &std::path::Path,
) -> Result<StdinContext> {
    let mut process_stdin = io::stdin().lock();
    if process_stdin.is_terminal() {
        return Ok(StdinContext {
            hash: ops::data::hash_bytes(&[]),
            broken_pipe: false,
            thread: None,
        });
    }

    let (sender, receiver) = ops::spool::create(directory);
    let stdin_broken = Arc::new(AtomicBool::new(false));
    let stdin_thread = thread::spawn({
        let stdin_broken = Arc::clone(&stdin_broken);
        move || {
            let result = receiver.forward(child_stdin)?;
            if result == TransferOutcome::BrokenPipe {
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
        if !sender.send(&chunk[..count])? {
            stdin_broken.store(true, Ordering::Release);
            break;
        }
        hasher.update(&chunk[..count]);
    }
    let broken_pipe = stdin_broken.load(Ordering::Acquire);
    drop(sender);

    Ok(StdinContext {
        hash: hasher.digest(),
        broken_pipe,
        thread: Some(stdin_thread),
    })
}

fn load_cache_data(
    config: &Config,
    cache: &CacheCursor<'_>,
    mut child: command::ManagedChild,
    runtime: &Runtime,
    prevalidated: Option<CacheData>,
) -> Result<CacheStatus> {
    if let Some(data) = prevalidated {
        let before_effects = runtime
            .effect_gate
            .as_ref()
            .is_none_or(|gate| gate.claim_replay());
        if before_effects {
            if child.try_wait()?.is_none() {
                command::kill_child(&child)?;
                child.wait()?;
            }
            command::reap_children();
            return Ok(CacheStatus::Valid(data));
        }
        if runtime
            .effect_gate
            .as_ref()
            .is_some_and(|gate| gate.has_live_effects())
        {
            super::speculation::stop_and_restore(config, runtime, &mut child, &data)?;
            return Ok(CacheStatus::Valid(data));
        }
        // An unresponsive/unattached tracer remains live; never require a report
        // from a process whose tracing handshake has not completed.
    }
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
            let exit_code = command::exit_code(child.wait()?);
            cache.clean()?;
            Ok(CacheStatus::Invalid(ExitCode(exit_code)))
        }
    }
}

fn save_command_data(
    config: &Config,
    command: &Command,
    cache: CacheCursor<'_>,
    runtime: &Runtime,
    exit_code: ExitCode,
) -> Result<ExitCode> {
    let cache_data = execution::record::capture(config, &cache, runtime, exit_code.0)?;
    cache.save_data(&cache_data)?;
    dependency::save_introspection(config, command, &cache_data)?;

    Ok(exit_code)
}
