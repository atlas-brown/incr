#![deny(rust_2018_idioms)]

mod annotation;
mod cache;
mod command;
mod config;
mod effect_gate;
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

#[derive(Clone, Debug, Parser)]
struct Arguments {
    #[arg(short = 't', long = "try")]
    try_command: Option<String>,
    #[arg(short = 'c', long = "cache")]
    cache_directory: Option<String>,
    #[arg(long = "observe")]
    observe_command: Option<String>,

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
    command: Vec<std::ffi::OsString>,
}

#[derive(Clone, Debug)]
struct Input {
    config: Config,
    command: Command,
    environment: HashMap<String, String>,
}

fn main() {
    ops::initialize_log_file();
    // Adopt tracees if a cancelled tracer exits before reaping them.
    if unsafe { libc::prctl(libc::PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) } != 0 {
        eprintln!(
            "Error: cannot establish child ownership: {}",
            std::io::Error::last_os_error()
        );
        process::exit(FAILURE_CODE.0);
    }
    let result = run();
    command::reap_children();
    match result {
        Ok(exit_code) => process::exit(exit_code.0),
        Err(error) => {
            eprintln!("Error: {error:#}");
            process::exit(FAILURE_CODE.0);
        }
    }
}

fn run() -> Result<ExitCode> {
    let (config, command, environment) = match parse_input()? {
        Some(input) => (input.config, input.command, input.environment),
        None => return Ok(SUCCESS_CODE),
    };
    if command.inherited_descriptors
        || (!config.full_tracing && annotation::skip_command(&command, &environment))
    {
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
        Err(error) => Err(error.context(format!("({command_string})"))),
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
                ops::file::path_to_string(&home_directory)?,
                DEFAULT_TRY_PATH,
            );
            (
                try_command.unwrap_or(default_try_command),
                home_directory.join(cache_directory.unwrap_or_else(|| DEFAULT_CACHE_PATH.to_owned())),
            )
        }
    };

    // Cache keys currently use UTF-8 strings. Preserve arbitrary Unix bytes by
    // executing such invocations directly instead of rejecting or corrupting them.
    let utf8_arguments = arguments
        .command
        .iter()
        .map(|s| s.to_str().map(str::to_owned))
        .collect::<Option<Vec<_>>>();
    let environment = env::vars_os()
        .map(|(k, v)| Some((k.into_string().ok()?, v.into_string().ok()?)))
        .collect::<Option<HashMap<_, _>>>();
    let (Some(command_arguments), Some(environment)) = (utf8_arguments, environment) else {
        use std::os::unix::process::CommandExt;
        let error = std::process::Command::new(&arguments.command[0])
            .args(&arguments.command[1..])
            .exec();
        eprintln!("{}: {error}", arguments.command[0].to_string_lossy());
        process::exit(if error.kind() == std::io::ErrorKind::NotFound {
            127
        } else {
            126
        });
    };
    let command = command::create(command_arguments, &environment)?;
    let trace_type = if arguments.full_tracing {
        if arguments.observe_command.is_some() {
            crate::config::TraceType::Observe
        } else {
            crate::config::TraceType::Sandbox
        }
    } else {
        execution::get_trace_type(
            &cache_directory,
            &command,
            arguments.observe_command.as_deref(),
            !arguments.skip_introspection,
        )
    };
    let config = Config {
        try_command,
        cache_directory,
        trace_type,
        observe_command: arguments.observe_command,

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
