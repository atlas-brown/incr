#![deny(rust_2018_idioms)]

mod annotation;
mod cache;
mod command;
mod config;
mod execution;
mod ops;
mod scripts;

use anyhow::{Result, anyhow};
use clap::Parser;
use std::collections::HashMap;
use std::env;
use std::path::PathBuf;
use std::process;

use crate::command::Command;
use crate::config::Config;
use crate::config::{DEFAULT_CACHE_PATH, DEFAULT_TRY_PATH};
use crate::execution::{batch_executor, chunk_executor, skip_executor, stream_executor};
use crate::ops::{ExitCode, FAILURE_CODE, SUCCESS_CODE};

/// CLI arguments parsed by clap. The trailing `command` captures the wrapped command and its args.
#[derive(Clone, Debug, Parser)]
struct Arguments {
    #[arg(short = 't', long = "try")]
    try_command: Option<String>,
    #[arg(short = 'c', long = "cache")]
    cache_directory: Option<String>,

    #[arg(short = 'b', long = "batch_executor")]
    batch_executor: bool,
    #[arg(short = 's', long = "short_circuit")]
    short_circuit: bool,
    #[arg(short = 'z', long = "compress_output")]
    compress_output: bool,
    #[arg(short = 'f', long = "full_tracing")]
    full_tracing: bool,
    #[arg(short = 'a', long = "enable_annotations")]
    enable_annotations: bool,
    #[arg(short = 'o', long = "skip_introspection")]
    skip_introspection: bool,

    #[arg(trailing_var_arg = true)]
    command: Vec<String>,
}

#[derive(Clone, Debug)]
struct Input {
    config: Config,
    command: Command,
    environment: HashMap<String, String>,
}

fn main() {
    ops::initialize_log_file();
    match run() {
        Ok(exit_code) => process::exit(exit_code.0),
        Err(error) => {
            eprintln!("Error: {error}");
            process::exit(FAILURE_CODE.0);
        }
    }
}

/// Parses input, selects an executor (skip, chunk, stream, or batch), and runs the command.
fn run() -> Result<ExitCode> {
    let (config, command, environment) = match parse_input()? {
        Some(input) => (input.config, input.command, input.environment),
        None => return Ok(SUCCESS_CODE),
    };
    if !config.full_tracing && annotation::skip_command(&command, &environment) {
        return Err(skip_executor::execute(&command));
    }

    let chunk = !config.full_tracing && config.enable_annotations && annotation::check_stateless(&command);
    let command_string = command.join_string()?;
    let result = if chunk {
        chunk_executor::execute(config, command)
    } else if !config.batch_executor {
        stream_executor::execute(&config, &command)
    } else {
        batch_executor::execute(&config, &command)
    };

    match result {
        Ok(code) => Ok(code),
        Err(error) => Err(anyhow!("({command_string}) {error}")),
    }
}

/// Resolves CLI args into a [`Config`], [`Command`], and environment. Returns `None` if no
/// command was provided. Falls back to `$HOME`-relative defaults for `--try` and `--cache`.
fn parse_input() -> Result<Option<Input>> {
    let arguments = Arguments::parse();
    if arguments.command.is_empty() {
        return Ok(None);
    }

    let (try_command, cache_directory) = match (arguments.try_command, arguments.cache_directory) {
        (Some(try_command), Some(cache_directory)) => (try_command, PathBuf::from(cache_directory)),
        (try_command, cache_directory) => {
            let home_directory =
                env::home_dir().ok_or_else(|| anyhow!("Could not resolve home directory"))?;
            let default_try_command = format!(
                "{}/{}",
                ops::file::path_to_string(&home_directory)?,
                DEFAULT_TRY_PATH,
            );
            (
                try_command.unwrap_or(default_try_command),
                home_directory.join(cache_directory.unwrap_or_else(|| DEFAULT_CACHE_PATH.to_owned())),
            )
        }
    };

    let environment = env::vars().collect::<HashMap<_, _>>();
    let command = command::create(arguments.command, &environment)?;
    let trace_type = execution::get_trace_type(&cache_directory, &command);
    let config = Config {
        try_command,
        cache_directory,
        trace_type,

        batch_executor: arguments.batch_executor,
        short_circuit: arguments.short_circuit,
        compress_output: arguments.compress_output,
        full_tracing: arguments.full_tracing,
        enable_annotations: arguments.enable_annotations,
        skip_introspection: arguments.skip_introspection,
    };

    Ok(Some(Input {
        config,
        command,
        environment,
    }))
}
