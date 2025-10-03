use anyhow::{Result, anyhow};
use std::io::{self, IsTerminal, Read, Write};

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, ChildContext, Command, Output};
use crate::config::Config;
use crate::ops::{BROKEN_PIPE_CODE, ExitCode};

#[derive(Clone, Debug)]
enum CommandResult {
    Completed(CacheData),
    Broken,
}

pub fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let mut stdin = Vec::new();
    {
        let mut process_stdin = io::stdin().lock();
        if !process_stdin.is_terminal() {
            process_stdin.read_to_end(&mut stdin)?;
        }
    }

    let cache = CacheCursor::new(command, &stdin)?;
    cache.create_directory()?;
    if let Some(cached_data) = cache.load_data()?
        && command::check_read_dependencies(&cached_data.read_dependencies)?
    {
        return output_cached_data(&cache, &cached_data);
    }

    cache.clean_sandbox_directory()?;
    cache.clean_data()?;
    let data = match run_command(config, command, &cache, &stdin)? {
        CommandResult::Completed(data) => data,
        CommandResult::Broken => return Ok(BROKEN_PIPE_CODE),
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
    let sandbox_directory = cache.get_sandbox_directory();
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = command::spawn_command(config, command, &sandbox_directory)?;

    {
        let mut child_stdin = child.stdin.take().unwrap();
        child_stdin.write_all(stdin)?;
        child_stdin.flush()?;
    }

    let exit_code = child.wait()?.code().unwrap();
    let stdout = stdout_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let stderr = stderr_thread.join().map_err(|e| anyhow!("{e:?}"))??;
    let (stdout, stderr) = match (stdout, stderr) {
        (Output::Completed(stdout), Output::Completed(stderr)) => (stdout, stderr),
        (Output::BrokenPipe, _) | (_, Output::BrokenPipe) => {
            cache.clean_sandbox_directory()?;
            return Ok(CommandResult::Broken);
        }
    };

    let (read_set, write_set) = command::parse_trace(&sandbox_directory)?;
    let read_dependencies = command::get_read_dependencies(read_set, &write_set)?;
    cache.extract_sandbox_output()?;
    if !write_set.is_empty() {
        cache.commit_output()?;
    }

    Ok(CommandResult::Completed(CacheData {
        exit_code,
        stdout,
        stderr,
        read_dependencies,
        write_outputs: write_set,
    }))
}

fn output_cached_data(cache: &CacheCursor<'_>, data: &CacheData) -> Result<ExitCode> {
    {
        let mut process_stdout = io::stdout().lock();
        process_stdout.write_all(&data.stdout)?;
        process_stdout.flush()?;
    }
    {
        let mut process_stderr = io::stderr().lock();
        process_stderr.write_all(&data.stderr)?;
        process_stderr.flush()?;
    }
    if !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    Ok(ExitCode(data.exit_code))
}
