use anyhow::Result;
use bincode::{Decode, Encode};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};

use crate::command::Command;
use crate::config::{
    CACHE_DIRECTORY, CHUNK_SIZE, COMMIT_DIRECTORY, DATA_FILE, DEBUG, DEBUG_FILE, OUTPUT_DIRECTORY,
    SANDBOX_DIRECTORY, SUDO_SANDBOX, TRY_COMMAND,
};
use crate::ops;

#[derive(Clone, Debug)]
pub(crate) struct CacheCursor<'c> {
    info: CacheInfo<'c>,
    directory: PathBuf,
}

impl<'c> CacheCursor<'c> {
    pub(crate) fn new(command: &'c Command, stdin: &'c [u8]) -> Result<Self> {
        let info = CacheInfo {
            name: &command.name,
            arguments: &command.arguments,
            environment: &command.environment,
            stdin,
        };

        let mut hasher = Sha256::new();
        hasher.update(ops::encode_to_vec(&info)?);
        let directory_name = format!("cache_{:x}", hasher.finalize());
        let directory = Path::new(CACHE_DIRECTORY).join(directory_name);

        Ok(Self { info, directory })
    }

    pub(crate) fn get_sandbox_directory(&self) -> PathBuf {
        self.directory.join(SANDBOX_DIRECTORY)
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
            let mut file_writer = BufWriter::with_capacity(CHUNK_SIZE, file);
            serde_json::to_writer_pretty(&mut file_writer, &self.info)?;
            file_writer.flush()?;
        }

        Ok(())
    }

    pub(crate) fn clean_sandbox_directory(&self) -> Result<()> {
        remove_sandbox(&self.directory.join(SANDBOX_DIRECTORY))
    }

    pub(crate) fn clean_data(&self) -> Result<()> {
        let data_file = ops::add_data_extension(DATA_FILE.to_owned());
        ops::ignore_not_found(fs::remove_dir_all(self.directory.join(OUTPUT_DIRECTORY)))?;
        ops::ignore_not_found(fs::remove_dir_all(self.directory.join(COMMIT_DIRECTORY)))?;
        ops::ignore_not_found(fs::remove_file(data_file))?;
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
            .args(["commit", ops::path_to_string(&commit_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        fs::remove_dir_all(&commit_directory)?;

        Ok(())
    }

    pub(crate) fn load_data(&self) -> Result<Option<CacheData>> {
        ops::decode_from_file(&self.directory, DATA_FILE.to_owned())
    }

    pub(crate) fn save_data(&self, data: &CacheData) -> Result<()> {
        ops::encode_to_file(data, &self.directory, DATA_FILE.to_owned())
    }
}

#[derive(Clone, Debug, Encode, Serialize)]
struct CacheInfo<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    #[serde(with = "ops::serialize_byte_slice")]
    stdin: &'c [u8],
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Serialize)]
pub(crate) struct CacheData {
    pub(crate) exit_code: i32,
    #[serde(with = "ops::serialize_byte_vec")]
    pub(crate) stdout: Vec<u8>,
    #[serde(with = "ops::serialize_byte_vec")]
    pub(crate) stderr: Vec<u8>,
    pub(crate) read_dependencies: HashMap<PathBuf, DependencyKey>,
    pub(crate) write_outputs: HashSet<PathBuf>,
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Serialize)]
pub(crate) enum DependencyKey {
    DoesNotExist,
    Timestamp(u128),
    Hash(String),
}

pub(crate) fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
        if !sandbox_directory.exists() {
            return Ok(());
        }
        ShellCommand::new("sudo")
            .args(["rm", "-rf", ops::path_to_string(sandbox_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
    } else {
        ops::ignore_not_found(fs::remove_dir_all(sandbox_directory))?;
    }
    Ok(())
}
