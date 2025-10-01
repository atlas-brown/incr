use anyhow::{Result, bail};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs::{self, File};
use std::path::PathBuf;

use crate::config::{CACHE_DIRECTORY, DEBUG, DEBUG_FILE};

#[derive(Debug, Deserialize, Serialize)]
pub struct CacheData {
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
struct CommandInfo {
    name: String,
}

#[derive(Debug, Serialize)]
struct InvocationInfo {
    arguments: Vec<String>,
    environment: HashMap<String, String>,
    stdin: Vec<u8>,
}

pub fn create_command_directory(command_name: &str) -> Result<()> {
    let mut path = PathBuf::from(CACHE_DIRECTORY);
    if !DEBUG {
        path.push(hash_path(command_name));
    } else {
        path.push(command_name);
    }

    if path.exists() {
        if !path.is_dir() {
            bail!("Command cache is not a directory");
        }
        return Ok(());
    }

    fs::create_dir_all(&path)?;
    if DEBUG {
        path.push(DEBUG_FILE);
        serde_json::to_writer_pretty(
            File::create(&path)?,
            &CommandInfo {
                name: command_name.to_owned(),
            },
        )?;
    }

    Ok(())
}

fn hash_path(name: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(name);
    format!("{:x}", hasher.finalize())
}
