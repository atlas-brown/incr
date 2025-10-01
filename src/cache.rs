use anyhow::Result;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap};
use std::fs::{self, File};
use std::path::PathBuf;

use crate::command_io::Command;
use crate::config::{CACHE_DIRECTORY, DEBUG, DEBUG_FILE};

#[derive(Debug)]
pub struct CacheCursor {
    info: CacheInfo,
    directory: PathBuf,
}

impl CacheCursor {
    pub fn new(command_name: String) -> Self {
        let mut directory = PathBuf::from(CACHE_DIRECTORY);
        if !DEBUG {
            directory.push(hash_string(&command_name));
        } else {
            directory.push(&command_name);
        }
        Self {
            info: CacheInfo { command_name },
            directory,
        }
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
            serde_json::to_writer_pretty(File::create(&debug_file)?, &self.info)?;
        }

        Ok(())
    }

    pub fn get_invocation<'c>(
        &self,
        command: &'c Command,
        stdin: &'c [u8],
    ) -> Result<InvocationCursor<'c>> {
        InvocationCursor::new(self.directory.clone(), command, stdin)
    }
}

#[derive(Debug, Serialize)]
struct CacheInfo {
    command_name: String,
}

#[derive(Debug)]
pub struct InvocationCursor<'c> {
    info: InvocationInfo<'c>,
    directory: PathBuf,
}

impl<'c> InvocationCursor<'c> {
    pub fn new(mut directory: PathBuf, command: &'c Command, stdin: &'c [u8]) -> Result<Self> {
        let info = InvocationInfo {
            arguments: &command.arguments[1..],
            environment: &command.environment,
            stdin,
        };
        let info_string = serde_json::to_string(&info)?;
        directory.push(hash_string(&info_string));
        Ok(Self { info, directory })
    }
}

#[derive(Debug, Serialize)]
struct InvocationInfo<'c> {
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    #[serde(with = "serialize_bytes")]
    stdin: &'c [u8],
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

fn hash_string(string: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(string);
    format!("{:x}", hasher.finalize())
}

mod serialize_bytes {
    use base64::prelude::*;
    use serde::{Serialize, Serializer};

    pub fn serialize<S>(bytes: &[u8], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let encoded = BASE64_STANDARD.encode(bytes);
        String::serialize(&encoded, serializer)
    }
}
