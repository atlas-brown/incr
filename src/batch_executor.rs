use anyhow::{Result, anyhow};
use std::io::{self, ErrorKind, IsTerminal, Read, Write};

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, ChildContext, ChildEnv, Command, Output};
use crate::config::Config;
use crate::execution;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode, debug_log};

#[derive(Clone, Debug)]
enum CommandResult {
    Completed(CacheData),
    BrokenPipe,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    debug_log!(
        "[{}] Starting batch command (skip_sandbox={})",
        command.name,
        config.skip_sandbox,
    );

    let mut stdin = Vec::new();
    {
        let mut process_stdin = io::stdin().lock();
        if !process_stdin.is_terminal() {
            process_stdin.read_to_end(&mut stdin)?;
        }
    }
    debug_log!("[{}] Collected all stdin", command.name);

    let cache = CacheCursor::new(command, &stdin)?;
    cache.create_directory()?;
    if let Some(cached_data) = cache.load_data()?
        && execution::check_cache_valid(&cache, &cached_data)?
    {
        return output_cached_data(config, command, &cache, &cached_data);
    }

    cache.clean_sandbox_directory()?;
    cache.clean_data()?;
    let data = match run_command(config, command, &cache, &stdin)? {
        CommandResult::Completed(data) => data,
        CommandResult::BrokenPipe => return Ok(BROKEN_PIPE_CODE),
    };
    cache.save_data(&data)?;

    Ok(ExitCode(data.exit_code))
}

fn run_command(
    config: &Config,
    command: &Command,
    cache: &CacheCursor<'_>,
    stdin: &[u8],
) -> Result<CommandResult> {
    let child_env = if !config.skip_sandbox {
        ChildEnv::Sandbox(cache.get_sandbox_directory())
    } else {
        ChildEnv::TraceFile(cache.get_trace_file())
    };
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
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (stdout, stderr) = match (stdout, stderr) {
        (Output::Completed(stdout), Output::Completed(stderr)) => (stdout, stderr),
        (Output::BrokenPipe, _) | (_, Output::BrokenPipe) => {
            if let ChildEnv::Sandbox(_) = child_env {
                cache.clean_sandbox_directory()?;
            }
            return Ok(CommandResult::BrokenPipe);
        }
    };
    debug_log!("[{}] Loaded child outputs", command.name);

    let (read_set, write_set) = execution::parse_trace(&child_env)?;
    let read_dependencies = execution::get_read_dependencies(read_set, &write_set)?;
    if let ChildEnv::Sandbox(_) = child_env {
        cache.extract_sandbox_output()?;
        if !write_set.is_empty() {
            cache.commit_output()?;
        }
    }
    debug_log!("[{}] Extracted dependencies and committed files", command.name);

    Ok(CommandResult::Completed(CacheData {
        exit_code,
        stdout,
        stderr,
        read_dependencies,
        write_outputs: write_set,
    }))
}

fn output_cached_data(
    config: &Config,
    command: &Command,
    cache: &CacheCursor<'_>,
    data: &CacheData,
) -> Result<ExitCode> {
    let stdout_completed = ops::output_data(&data.stdout, io::stdout().lock())?;
    let stderr_completed = ops::output_data(&data.stderr, io::stderr().lock())?;

    if !config.complete_execution && (!stdout_completed || !stderr_completed) {
        return Ok(BROKEN_PIPE_CODE);
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    debug_log!("[{}] Outputted cached data and committed files", command.name);

    Ok(ExitCode(data.exit_code))
}
