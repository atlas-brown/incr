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

const EXECUTOR: Executor = Executor::Stream;

#[allow(unused)]
#[derive(Clone, Copy, Debug)]
enum Executor {
    Batch,
    Stream,
}

#[derive(Clone, Debug, Parser)]
struct Arguments {
    #[arg(short = 't', long = "try")]
    try_command: Option<String>,
    #[arg(short = 'c', long = "cache")]
    cache_directory: Option<String>,
    #[arg(short = 'f', long = "force_cache")]
    force_cache: bool,
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

fn run() -> Result<ExitCode> {
    let (config, command, environment) = match parse_input()? {
        Some(input) => (input.config, input.command, input.environment),
        None => return Ok(SUCCESS_CODE),
    };
    if !config.force_cache && annotation::skip_command(&command, &environment) {
        return Err(skip_executor::run(&command));
    }

    let result = if annotation::check_stateless(&command) {
        chunk_executor::run(&config, &command)
    } else {
        match EXECUTOR {
            Executor::Batch => batch_executor::run(&config, &command),
            Executor::Stream => stream_executor::run(&config, &command),
        }
    };

    match result {
        Ok(code) => Ok(code),
        Err(error) => Err(anyhow!("({}) {}", command.join_string()?, error)),
    }
}

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
                ops::files::path_to_string(&home_directory)?,
                DEFAULT_TRY_PATH,
            );
            (
                try_command.unwrap_or(default_try_command),
                home_directory.join(cache_directory.unwrap_or_else(|| DEFAULT_CACHE_PATH.to_owned())),
            )
        }
    };

    let environment = env::vars().collect::<HashMap<_, _>>();
    let command = command::get_command(arguments.command, &environment)?;
    let trace_type = execution::get_trace_type(&cache_directory, &command);
    let config = Config {
        try_command,
        cache_directory,
        trace_type,
        complete_execution: true, // TODO: add a flag
        compress: false,          // TODO: add a flag
        force_cache: arguments.force_cache,
    };

    Ok(Some(Input {
        config,
        command,
        environment,
    }))
}
