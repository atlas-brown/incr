#![deny(rust_2018_idioms)]

mod batch_executor;
mod cache;
mod command;
mod config;
mod ops;
mod stream_executor;

use std::process::ExitCode;

const EXECUTOR: Executor = Executor::Stream;

#[allow(unused)]
#[derive(Clone, Copy, Debug)]
enum Executor {
    Batch,
    Stream,
}

fn main() -> ExitCode {
    let command = match command::get_command() {
        Ok(Some(command)) => command,
        Ok(None) => return ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Error: {error}");
            return ExitCode::FAILURE;
        }
    };
    let result = match EXECUTOR {
        Executor::Batch => batch_executor::run(command),
        Executor::Stream => stream_executor::run(command),
    };
    match result {
        Ok(exit_code) => exit_code,
        Err(error) => {
            eprintln!("Error: {error}");
            ExitCode::FAILURE
        }
    }
}
