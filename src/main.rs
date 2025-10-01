mod batch_executor;
mod cache;
mod command;
mod config;
mod ops;

use std::process::ExitCode;

fn main() -> ExitCode {
    let command = match command::get_command() {
        Ok(Some(command)) => command,
        Ok(None) => return ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Error: {error}");
            return ExitCode::FAILURE;
        }
    };
    match batch_executor::run(command) {
        Ok(exit_code) => exit_code,
        Err(error) => {
            eprintln!("Error: {error}");
            ExitCode::FAILURE
        }
    }
}
