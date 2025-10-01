use anyhow::{Result, anyhow};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};

use crate::command::Command;
use crate::config::{
    CACHE_DIRECTORY, COMMIT_DIRECTORY, DATA_FILE, DEBUG, DEBUG_FILE, OUTPUT_DIRECTORY,
    SANDBOX_DIRECTORY, SUDO_SANDBOX, TRY_COMMAND,
};
use crate::ops;

#[derive(Debug)]
pub struct CacheCursor {
    info: CacheInfo,
    directory: PathBuf,
}

impl CacheCursor {
    pub fn new(command_name: String) -> Self {
        let mut directory = PathBuf::from(CACHE_DIRECTORY);
        if !DEBUG {
            directory.push(ops::hash_string(&command_name));
        } else {
            directory.push(&command_name);
        }
        Self {
            info: CacheInfo { command_name },
            directory,
        }
    }

    pub fn create_directory(&self) -> Result<()> {
        create_cache_directory(&self.directory, &self.info)
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
            arguments: &command.arguments,
            environment: &command.environment,
            stdin,
        };
        let info_string = serde_json::to_string(&info)?;
        directory.push(ops::hash_string(&info_string));
        Ok(Self { info, directory })
    }

    pub fn get_sandbox_directory(&self) -> PathBuf {
        return self.directory.join(SANDBOX_DIRECTORY);
    }

    pub fn create_directory(&self) -> Result<()> {
        create_cache_directory(&self.directory, &self.info)
    }

    pub fn clean(&self) -> Result<()> {
        remove_sandbox(&self.directory.join(SANDBOX_DIRECTORY))?;
        ops::ignore_not_found(fs::remove_dir_all(self.directory.join(OUTPUT_DIRECTORY)))?;
        ops::ignore_not_found(fs::remove_dir_all(self.directory.join(COMMIT_DIRECTORY)))?;
        ops::ignore_not_found(fs::remove_file(self.directory.join(DATA_FILE)))?;
        Ok(())
    }

    pub fn extract_sandbox_output(&self) -> Result<()> {
        let sandbox_directory = self.directory.join(SANDBOX_DIRECTORY);
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);

        fs::create_dir_all(&output_directory)?;
        fs::rename(
            sandbox_directory.join("upperdir"),
            output_directory.join("upperdir"),
        )?;
        fs::rename(
            sandbox_directory.join("ignore"),
            output_directory.join("ignore"),
        )?;
        remove_sandbox(&sandbox_directory)?;

        Ok(())
    }

    pub fn commit_output(&self) -> Result<()> {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        let commit_directory = self.directory.join(COMMIT_DIRECTORY);

        ShellCommand::new("cp")
            .args(&[
                "-r",
                ops::path_to_string(&output_directory)?,
                ops::path_to_string(&commit_directory)?,
            ])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;

        ShellCommand::new(TRY_COMMAND)
            .args(&["commit", ops::path_to_string(&commit_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;

        Ok(())
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
pub struct InvocationResult {
    pub exit_code: i32,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub read_dependencies: HashMap<PathBuf, FileKey>,
    pub write_outputs: HashSet<PathBuf>,
}

#[derive(Debug, Deserialize, Serialize)]
pub enum FileKey {
    Timestamp(u128),
    Hash(String),
}

fn create_cache_directory<I>(directory: &Path, info: &I) -> Result<()>
where
    I: Serialize,
{
    if directory.exists() {
        if directory.is_dir() {
            return Ok(());
        }
        fs::remove_file(directory)?;
    }

    fs::create_dir_all(directory)?;
    if DEBUG {
        let debug_file = directory.join(DEBUG_FILE);
        serde_json::to_writer_pretty(File::create(&debug_file)?, info)?;
    }

    Ok(())
}

fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
        ShellCommand::new("sudo")
            .args(&["rm", "-rf", ops::path_to_string(&sandbox_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
    } else {
        ops::ignore_not_found(fs::remove_dir_all(&sandbox_directory))?;
    }
    Ok(())
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
