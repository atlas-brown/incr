use anyhow::{Result, bail};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs::{self, File};
use std::path::{Path, PathBuf};

use crate::command_io::Command;
use crate::config::{CACHE_DIRECTORY, DEBUG, DEBUG_FILE};

pub struct CacheCursor {
    command: Command,
    directory: PathBuf,
}

impl CacheCursor {
    pub fn new(command: Command) -> Self {
        let mut directory = PathBuf::from(CACHE_DIRECTORY);
        if !DEBUG {
            directory.push(hash_path(&command.name));
        } else {
            directory.push(&command.name);
        }
        Self { command, directory }
    }

    pub fn create_directory(&self) -> Result<()> {
        if self.directory.exists() {
            if self.directory.is_dir() {
                return Ok(());
            }
            fs::remove_file(&self.directory)?;
        }

        fs::create_dir_all(&self.directory)?;
        if DEBUG {
            let debug_file = self.directory.join(DEBUG_FILE);
            serde_json::to_writer_pretty(
                File::create(&debug_file)?,
                &CacheInfo {
                    name: self.command.name.to_owned(),
                },
            )?;
        }

        Ok(())
    }
}

pub struct InvocationCursor {
    info: InvocationInfo,
    directory: PathBuf,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct InvocationData {
    pub exit_code: i32,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub read_dependencies: HashMap<PathBuf, FileKey>,
    pub write_outputs: Vec<PathBuf>,
}

#[derive(Debug, Deserialize, Serialize)]
pub enum FileKey {
    Timestamp(u128),
    Hash(String),
}

#[derive(Debug, Serialize)]
struct CacheInfo {
    name: String,
}

#[derive(Debug, Serialize)]
struct InvocationInfo {
    arguments: Vec<String>,
    environment: HashMap<String, String>,
    stdin: Vec<u8>,
}

fn hash_path(name: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(name);
    format!("{:x}", hasher.finalize())
}
