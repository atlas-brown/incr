use anyhow::{Result, anyhow};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, IsTerminal, Read, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::thread;

use crate::cache::{CacheCursor, CacheData};
use crate::command::{self, Command};
use crate::config::CACHE_DIRECTORY;
use crate::ops;

pub fn run(command: Command) -> Result<ExitCode> {
    let sandbox_directory = create_sandbox_directory(&command)?;
    let mut child = command::spawn_command(&command, &sandbox_directory)?;

    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn(move || command::capture_stream(child_stdout, io::stdout()));
    let stderr_thread = thread::spawn(move || command::capture_stream(child_stderr, io::stderr()));

    let stdin = {
        let child_stdin = child.stdin.take().unwrap();
        let process_stdin = io::stdin().lock();
        command::capture_stream(process_stdin, child_stdin)?
    };
    println!("got stdin: {stdin:?}");

    unimplemented!()
}

fn create_sandbox_directory(command: &Command) -> Result<PathBuf> {
    let mut hasher = Sha256::new();
    hasher.update(ops::encode_to_vec(command)?);
    let directory_name = format!("sandbox_{:x}", hasher.finalize());
    let directory = Path::new(CACHE_DIRECTORY).join(directory_name);

    if directory.is_dir() {
        fs::remove_dir_all(&directory)?;
    } else if directory.is_file() {
        fs::remove_file(&directory)?;
    }
    fs::create_dir_all(&directory)?;

    Ok(directory)
}
