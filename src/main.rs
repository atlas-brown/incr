mod batch_executor;
mod cache;
mod command_io;
mod config;

use std::process::ExitCode;

fn main() -> ExitCode {
    let command = match command_io::get_command() {
        Ok(Some(command)) => command,
        Ok(None) => return ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            return ExitCode::FAILURE;
        }
    };

    println!("{command:?}");

    ExitCode::SUCCESS
}
