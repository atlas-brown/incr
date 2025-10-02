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

    println!("running: {command:?} {sandbox_directory:?}");
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
