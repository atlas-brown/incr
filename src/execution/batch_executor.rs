use anyhow::{Result, anyhow};
use std::io::{self, ErrorKind, IsTerminal, Read, Write};

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildEnv, ChildOutput, Command, EnvType};
use crate::config::{Config, TraceType};
use crate::execution;
use crate::ops::{BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Clone, Debug)]
enum CommandResult {
    Completed(CacheData),
    BrokenPipe,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    debug_log!(
        "[{}] Starting batch command (trace_type={})",
        command.name,
        config.trace_type,
    );

    let mut stdin = Vec::new();
    {
        let mut process_stdin = io::stdin().lock();
        if !process_stdin.is_terminal() {
            process_stdin.read_to_end(&mut stdin)?;
        }
    }
    debug_log!("[{}] Collected all stdin", command.name);

    let cache = CacheCursor::from_stdin(command, &stdin)?;
    cache.create_directory()?;
    if let Some(cached_data) = cache.load_data()?
        && execution::check_cache_valid(&cache, &cached_data)?
    {
        return output_cached_data(config, command, &cache, &cached_data);
    }

    cache.clean_sandbox_directory()?;
    cache.clean_data_files()?;
    let data = match run_command(config, command, &cache, &stdin)? {
        CommandResult::Completed(data) => data,
        CommandResult::BrokenPipe => return Ok(BROKEN_PIPE_CODE),
    };
    cache.save_data(&data)?;
    debug_log!("[{}] Saved command data", command.name);

    Ok(ExitCode(data.exit_code))
}

fn run_command(
    config: &Config,
    command: &Command,
    cache: &CacheCursor<'_>,
    stdin: &[u8],
) -> Result<CommandResult> {
    let child_env = create_child_environment(config, cache);
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &child_env)?;
    debug_log!("[{}] Spawned batch child", command.name);

    {
        let mut child_stdin = child.stdin.take().unwrap();
        if let Err(error) = child_stdin.write_all(stdin)
            && error.kind() != ErrorKind::BrokenPipe
        {
            return Err(error.into());
        }
    }
    debug_log!("[{}] Finished sending stdin to child", command.name);

    let exit_code = child.wait()?.code().unwrap();
    let stdout_result = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr_result = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    if stdout_result == ChildOutput::BrokenPipe || stderr_result == ChildOutput::BrokenPipe {
        clean_child_environment(cache, &child_env)?;
        return Ok(CommandResult::BrokenPipe);
    }
    debug_log!("[{}] Saved child outputs", command.name);

    let (read_set, write_set) = execution::parse_trace(&child_env)?;
    let read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    if let EnvType::Sandbox(_) = &child_env.typ {
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
    }
    debug_log!("[{}] Extracted dependencies and committed files", command.name);

    Ok(CommandResult::Completed(CacheData {
        exit_code,
        read_dependencies,
        write_outputs: write_set,
    }))
}

fn create_child_environment(config: &Config, cache: &CacheCursor<'_>) -> ChildEnv {
    ChildEnv {
        typ: match config.trace_type {
            TraceType::Sandbox => EnvType::Sandbox(cache.get_sandbox_directory()),
            TraceType::TraceFile => EnvType::TraceFile(cache.get_trace_file()),
            TraceType::Nothing => EnvType::Nothing,
        },
        stdout_file: cache.get_stdout_file(),
        stderr_file: cache.get_stderr_file(),
    }
}

fn clean_child_environment(cache: &CacheCursor<'_>, child_env: &ChildEnv) -> Result<()> {
    cache.clean_output_files()?;
    match &child_env.typ {
        EnvType::Sandbox(_) => cache.clean_sandbox_directory()?,
        EnvType::TraceFile(_) => cache.clean_trace_file()?,
        EnvType::Nothing => (),
    }
    Ok(())
}

fn output_cached_data(
    config: &Config,
    command: &Command,
    cache: &CacheCursor<'_>,
    data: &CacheData,
) -> Result<ExitCode> {
    let stdout_completed = execution::output_data(&cache.get_stdout_file(), 0, &mut io::stdout().lock())?;
    let stderr_completed = execution::output_data(&cache.get_stderr_file(), 0, &mut io::stderr().lock())?;
    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Outputted cached data and committed files", command.name);

    Ok(ExitCode(data.exit_code))
}
