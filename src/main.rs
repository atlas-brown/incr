#![deny(rust_2018_idioms)]

mod batch_executor;
mod cache;
mod command;
mod config;
mod ops;
mod stream_executor;

use anyhow::Result;
use std::process;

use crate::ops::ExitCode;

const EXECUTOR: Executor = Executor::Batch;

#[allow(unused)]
#[derive(Clone, Copy, Debug)]
enum Executor {
    Batch,
    Stream,
}

fn main() {
    match run() {
        Ok(exit_code) => process::exit(exit_code.0),
        Err(error) => {
            eprintln!("Error: {error}");
            process::exit(1);
        }
    }
}

fn run() -> Result<ExitCode> {
    let command = match command::get_command()? {
        Some(command) => command,
        None => return Ok(ExitCode(0)),
    };
    match EXECUTOR {
        Executor::Batch => batch_executor::run(command),
        Executor::Stream => stream_executor::run(command),
    }
}
