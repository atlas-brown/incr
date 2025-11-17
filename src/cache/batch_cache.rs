use anyhow::Result;
use bincode::{Decode, Encode};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};

use crate::command::Command;
use crate::config::{
    BUFFER_SIZE, COMMIT_DIRECTORY, Config, DATA_FILE, DEBUG, DEBUG_FILE, OUTPUT_DIRECTORY, SANDBOX_DIRECTORY,
    STDERR_FILE, STDOUT_FILE, SUDO_SANDBOX, TRACE_FILE,
};
use crate::ops;

#[derive(Clone, Debug)]
pub(crate) struct CacheCursor<'c> {
    directory: PathBuf,
    try_command: String,
    debug_info: CacheInfo<'c>,
}

impl<'c> CacheCursor<'c> {
    pub(crate) fn from_stdin(config: &Config, command: &'c Command, stdin: &'c [u8]) -> Result<Self> {
        let stdin_hash = ops::data::hash_bytes(stdin);
        let debug_info = CacheInfo {
            name: &command.name,
            arguments: &command.arguments,
            environment: &command.environment,
            stdin_hash,
            stdin: Some(stdin),
        };
        Self::with_info(config, command, stdin_hash, debug_info)
    }

    pub(crate) fn from_hash(config: &Config, command: &'c Command, stdin_hash: u64) -> Result<Self> {
        let debug_info = CacheInfo {
            name: &command.name,
            arguments: &command.arguments,
            environment: &command.environment,
            stdin_hash,
            stdin: None,
        };
        Self::with_info(config, command, stdin_hash, debug_info)
    }

    fn with_info(
        config: &Config,
        command: &'c Command,
        stdin_hash: u64,
        debug_info: CacheInfo<'c>,
    ) -> Result<Self> {
        let key_data = ops::data::encode_to_bytes(&CacheKey {
            name: &command.name,
            arguments: &command.arguments,
            environment: &command.environment,
            stdin_hash,
        })?;
        let hash = ops::data::hash_bytes(&key_data);
        Ok(Self {
            directory: config.cache_directory.join(format!("cache_{hash}")),
            try_command: config.try_command.clone(),
            debug_info,
        })
    }

    pub(crate) fn get_stdout_file(&self) -> PathBuf {
        self.directory.join(STDOUT_FILE)
    }

    pub(crate) fn get_stderr_file(&self) -> PathBuf {
        self.directory.join(STDERR_FILE)
    }

    pub(crate) fn get_sandbox_directory(&self) -> PathBuf {
        self.directory.join(SANDBOX_DIRECTORY)
    }

    pub(crate) fn get_trace_file(&self) -> PathBuf {
        self.directory.join(TRACE_FILE)
    }

    pub(crate) fn create_directory(&self) -> Result<()> {
        if self.directory.is_dir() {
            return Ok(());
        }
        if self.directory.is_file() {
            fs::remove_file(&self.directory)?;
        }

        fs::create_dir_all(&self.directory)?;
        if DEBUG {
            let file = File::create(self.directory.join(DEBUG_FILE))?;
            let mut file_writer = BufWriter::with_capacity(BUFFER_SIZE, file);
            serde_json::to_writer_pretty(&mut file_writer, &self.debug_info)?;
            file_writer.flush()?;
        }

        Ok(())
    }

    pub(crate) fn extract_sandbox_output(&self) -> Result<()> {
        let sandbox_directory = self.directory.join(SANDBOX_DIRECTORY);
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);

        fs::create_dir_all(&output_directory)?;
        fs::rename(
            sandbox_directory.join("upperdir"),
            output_directory.join("upperdir"),
        )?;
        fs::rename(sandbox_directory.join("ignore"), output_directory.join("ignore"))?;
        remove_sandbox(&sandbox_directory)?;

        Ok(())
    }

    pub(crate) fn commit_output(&self) -> Result<()> {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        let commit_directory = self.directory.join(COMMIT_DIRECTORY);

        ShellCommand::new("cp")
            .args([
                "-rp",
                ops::files::path_to_string(&output_directory)?,
                ops::files::path_to_string(&commit_directory)?,
            ])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        ShellCommand::new(&self.try_command)
            .args(["commit", ops::files::path_to_string(&commit_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        fs::remove_dir_all(&commit_directory)?;

        Ok(())
    }

    pub(crate) fn data_outputs_exist(&self) -> bool {
        self.get_stdout_file().is_file() && self.get_stderr_file().is_file()
    }

    pub(crate) fn file_outputs_exist(&self) -> bool {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        output_directory.is_dir()
    }

    pub(crate) fn clean_output_files(&self) -> Result<()> {
        ops::files::ignore_missing(fs::remove_file(self.get_stdout_file()))?;
        ops::files::ignore_missing(fs::remove_file(self.get_stderr_file()))?;
        Ok(())
    }

    pub(crate) fn clean_sandbox_directory(&self) -> Result<()> {
        remove_sandbox(&self.get_sandbox_directory())
    }

    pub(crate) fn clean_trace_file(&self) -> Result<()> {
        ops::files::ignore_missing(fs::remove_file(self.get_trace_file()))
    }

    pub(crate) fn clean_data_files(&self) -> Result<()> {
        let data_file = ops::files::add_data_extension(DATA_FILE.to_owned());
        ops::files::ignore_missing(fs::remove_file(data_file))?;
        ops::files::ignore_missing(fs::remove_dir_all(self.directory.join(OUTPUT_DIRECTORY)))?;
        ops::files::ignore_missing(fs::remove_dir_all(self.directory.join(COMMIT_DIRECTORY)))?;
        Ok(())
    }

    pub(crate) fn load_data(&self) -> Result<Option<CacheData>> {
        ops::data::decode_from_file(&self.directory, DATA_FILE.to_owned())
    }

    pub(crate) fn save_data(&self, data: &CacheData) -> Result<()> {
        ops::data::encode_to_file(data, &self.directory, DATA_FILE.to_owned())
    }
}

#[derive(Clone, Debug, Encode, Serialize)]
struct CacheInfo<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    stdin_hash: u64,
    #[serde(with = "ops::serialize_bytes")]
    stdin: Option<&'c [u8]>,
}

#[derive(Clone, Debug, Encode)]
struct CacheKey<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    stdin_hash: u64,
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Serialize)]
pub(crate) struct CacheData {
    pub(crate) compressed_output: bool,
    pub(crate) exit_code: i32,
    pub(crate) read_dependencies: HashMap<PathBuf, DependencyKey>,
    pub(crate) write_outputs: HashSet<PathBuf>,
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Eq, PartialEq, Serialize)]
pub(crate) enum DependencyKey {
    DoesNotExist,
    Timestamp(u128),
    Hash(u64),
}

pub(crate) fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
        if !sandbox_directory.exists() {
            return Ok(());
        }
        ShellCommand::new("sudo")
            .args(["rm", "-rf", ops::files::path_to_string(sandbox_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
    } else {
        ops::files::ignore_missing(fs::remove_dir_all(sandbox_directory))?;
    }
    Ok(())
}
