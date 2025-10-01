use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

use crate::config::{DEBUG_INFO, HASH_COMMANDS};

#[derive(Deserialize, Serialize)]
pub struct CacheData {
    pub exit_code: i32,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub read_dependencies: HashMap<PathBuf, FileKey>,
    pub write_outputs: Vec<PathBuf>,
}

#[derive(Deserialize, Serialize)]
pub enum FileKey {
    Timestamp(u128),
    Hash(String),
}

#[derive(Deserialize, Serialize)]
struct CommandInfo {
    command: String,
}

#[derive(Deserialize, Serialize)]
struct InvocationInfo {
    arguments: Vec<String>,
    environment: HashMap<String, String>,
    stdin: Vec<u8>,
}
