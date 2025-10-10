#![deny(rust_2018_idioms)]

mod batch_executor;
mod cache;
mod command;
mod config;
mod execution;
mod ops;
mod stream_executor;

use anyhow::Result;
use std::process;

use crate::config::Config;
use crate::ops::{ExitCode, FAILURE_CODE, SUCCESS_CODE};

const EXECUTOR: Executor = Executor::Stream;

#[allow(unused)]
#[derive(Clone, Copy, Debug)]
enum Executor {
    Batch,
    Stream,
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
    let command = match command::get_command()? {
        Some(command) => command,
        None => return Ok(SUCCESS_CODE),
    };
    let config = Config {
        skip_sandbox: execution::skip_sandbox(&command),
        complete_execution: true,
    };
    match EXECUTOR {
        Executor::Batch => batch_executor::run(&config, &command),
        Executor::Stream => stream_executor::run(&config, &command),
    }
}
