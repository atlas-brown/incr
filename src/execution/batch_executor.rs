use anyhow::{Result, anyhow};
use std::io::{self, ErrorKind, IsTerminal, Read, Write};

use crate::cache::batch_cache::{CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildOutput, Command, Runtime, RuntimeType};
use crate::config::{Config, TraceType};
use crate::execution;
use crate::ops::{BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Clone, Debug)]
enum CommandResult {
    Completed(CacheData),
    BrokenPipe,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
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
        && execution::check_cache_valid(&cache, &cached_data)?
    {
        debug_log!("Cache valid: {} {:?}", command.name, command.arguments);
        return output_cached_data(config, &cache, &cached_data);
    }
    debug_log!("Cache invalid: {} {:?}", command.name, command.arguments);

    cache.clean_sandbox_directory()?;
    cache.clean_data_files()?;
    let cache_data = match run_command(config, command, &cache, &stdin)? {
        CommandResult::Completed(data) => data,
        CommandResult::BrokenPipe => return Ok(BROKEN_PIPE_CODE),
    };
    cache.save_data(&cache_data)?;
    execution::save_introspection(config, command, &cache_data)?;

    Ok(ExitCode(cache_data.exit_code))
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
    } = command::spawn_command(config, command, &runtime)?;

    {
        let mut child_stdin = child.stdin.take().unwrap();
        if let Err(error) = child_stdin.write_all(stdin)
            && error.kind() != ErrorKind::BrokenPipe
        {
            return Err(error.into());
        }
    }

    let exit_code = child.wait()?.code().unwrap();
    let stdout_result = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr_result = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    if stdout_result == ChildOutput::BrokenPipe || stderr_result == ChildOutput::BrokenPipe {
        clean_child_runtime(cache, &runtime)?;
        return Ok(CommandResult::BrokenPipe);
    }

    let (read_set, mut write_set) = execution::parse_trace(&runtime)?;
    let mut read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    if let RuntimeType::Sandbox(_) = &runtime.typ {
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
    }
    execution::filter_dependencies(&mut read_dependencies, &mut write_set)?;

    Ok(CommandResult::Completed(CacheData {
        compressed_output: config.compress,
        exit_code,
        read_dependencies,
        write_outputs: write_set,
    }))
}

fn create_child_runtime(config: &Config, cache: &CacheCursor<'_>) -> Runtime {
    Runtime {
        typ: match config.trace_type {
            TraceType::Sandbox => RuntimeType::Sandbox(cache.get_sandbox_directory()),
            TraceType::TraceFile => RuntimeType::TraceFile(cache.get_trace_file()),
            TraceType::Nothing => RuntimeType::Nothing,
        },
        stdout_file: cache.get_stdout_file(),
        stderr_file: cache.get_stderr_file(),
    }
}

fn clean_child_runtime(cache: &CacheCursor<'_>, runtime: &Runtime) -> Result<()> {
    cache.clean_output_files()?;
    match &runtime.typ {
        RuntimeType::Sandbox(_) => cache.clean_sandbox_directory()?,
        RuntimeType::TraceFile(_) => cache.clean_trace_file()?,
        RuntimeType::Nothing => (),
    }
    Ok(())
}

fn output_cached_data(config: &Config, cache: &CacheCursor<'_>, data: &CacheData) -> Result<ExitCode> {
    let stdout_completed = execution::output_data(
        &cache.get_stdout_file(),
        0,
        &mut io::stdout().lock(),
        data.compressed_output,
    )?;
    let stderr_completed = execution::output_data(
        &cache.get_stderr_file(),
        0,
        &mut io::stderr().lock(),
        data.compressed_output,
    )?;

    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }

    Ok(ExitCode(data.exit_code))
}
