use anyhow::{Result, anyhow};
use std::io::{self, IsTerminal, Read, Write};
use std::process::ExitCode;
use std::thread;

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, Command};

pub fn run(command: Command) -> Result<ExitCode> {
    println!("running: {command:?}");
    unimplemented!()
}
