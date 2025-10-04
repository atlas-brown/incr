#![deny(rust_2018_idioms)]

mod batch_executor;
mod cache;
mod command;
mod config;
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
    let config = Config {
        complete_after_downstream_failure: true,
    };
    match run(&config) {
        Ok(exit_code) => process::exit(exit_code.0),
        Err(error) => {
            eprintln!("Error: {error}");
            process::exit(FAILURE_CODE.0);
        }
    }
}

fn run(config: &Config) -> Result<ExitCode> {
    let command = match command::get_command()? {
        Some(command) => command,
        None => return Ok(SUCCESS_CODE),
    };
    match EXECUTOR {
        Executor::Batch => batch_executor::run(config, &command),
        Executor::Stream => stream_executor::run(config, &command),
    }
}
