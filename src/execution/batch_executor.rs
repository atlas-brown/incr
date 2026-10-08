use anyhow::Result;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};

use crate::cache::CacheData;
use crate::cache::batch_cache::CacheCursor;
use crate::command::{self, ChildContext, Command, Runtime, RuntimeType};
use crate::config::{Config, TraceType};
use crate::execution;
use crate::execution::dependency;
use crate::execution::run::{self, OutputMetadata};
use crate::ops::{BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Clone, Debug)]
enum CommandResult {
    Completed { data: CacheData, broken_pipe: bool },
    BrokenPipe,
}

pub(crate) fn execute(config: &Config, command: &Command) -> Result<ExitCode> {
    let mut stdin = Vec::new();
    {
        let mut process_stdin = io::stdin().lock();
        if !process_stdin.is_terminal() {
            process_stdin.read_to_end(&mut stdin)?;
        }
    }

    let cache = CacheCursor::from_stdin(config, command, &stdin)?;
    cache.create_directory()?;
    if let Some(cached_data) = cache.load_data()?
        && dependency::check_cache_valid(&cache, &cached_data)?
    {
        debug_log!("Cache valid: {} {:?}", command.name, command.arguments);
        return run::replay(config, &cache, &cached_data, &OutputMetadata::default());
    }
    debug_log!("Cache invalid: {} {:?}", command.name, command.arguments);

    cache.clean()?;
    let (cache_data, broken_pipe) = match run_command(config, command, &cache, &stdin)? {
        CommandResult::Completed { data, broken_pipe } => (data, broken_pipe),
        CommandResult::BrokenPipe => return Ok(BROKEN_PIPE_CODE),
    };
    cache.save_data(&cache_data)?;
    dependency::save_introspection(config, command, &cache_data)?;

    Ok(if broken_pipe {
        BROKEN_PIPE_CODE
    } else {
        ExitCode(cache_data.exit_code)
    })
}

fn run_command(
    config: &Config,
    command: &Command,
    cache: &CacheCursor<'_>,
    stdin: &[u8],
) -> Result<CommandResult> {
    let runtime = create_child_runtime(config, cache);
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn(config, command, &runtime)?;

    {
        let mut child_stdin = child.stdin.take().unwrap();
        if let Err(error) = child_stdin.write_all(stdin)
            && error.kind() != ErrorKind::BrokenPipe
        {
            return Err(error.into());
        }
    }

    let exit_code = command::exit_code(child.wait()?);
    let Some(outputs) = run::join_stream_threads(None, stdout_thread, stderr_thread)? else {
        run::clean_child_runtime(&runtime)?;
        return Ok(CommandResult::BrokenPipe);
    };

    Ok(CommandResult::Completed {
        data: execution::record::capture(config, cache, &runtime, exit_code)?,
        broken_pipe: outputs.broken_pipe,
    })
}

fn create_child_runtime(config: &Config, cache: &CacheCursor<'_>) -> Runtime {
    let kind = match config.trace_type {
        TraceType::Sandbox => RuntimeType::Sandbox(cache.get_sandbox_directory()),
        TraceType::TraceFile => {
            if config.observe_command.is_some() {
                RuntimeType::TraceFile(cache.get_observe_trace_file())
            } else {
                RuntimeType::TraceFile(cache.get_trace_file())
            }
        }
        TraceType::Observe => RuntimeType::Observe(cache.get_observe_trace_file()),
        TraceType::Nothing => RuntimeType::Nothing,
    };
    Runtime {
        kind,
        stdout_file: cache.get_stdout_file(),
        stderr_file: cache.get_stderr_file(),
        effect_gate: None,
        snapshot_directory: None,
    }
}
