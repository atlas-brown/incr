use anyhow::Result;
use bincode::{Decode, Encode};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufReader, BufWriter, ErrorKind, Write};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};

use crate::command::Command;
use crate::config::{
    CACHE_DIRECTORY, CHUNK_SIZE, COMMIT_DIRECTORY, DATA_FILE, DEBUG, DEBUG_FILE, OUTPUT_DIRECTORY,
    SANDBOX_DIRECTORY, SUDO_SANDBOX, TRY_COMMAND,
};
use crate::ops;

#[derive(Debug)]
pub struct CacheCursor<'c> {
    info: CacheInfo<'c>,
    directory: PathBuf,
}

impl<'c> CacheCursor<'c> {
    pub fn new(command: &'c Command, stdin: &'c [u8]) -> Result<Self> {
        let info = CacheInfo {
            name: &command.name,
            arguments: &command.arguments,
            environment: &command.environment,
            stdin,
        };

        let mut hasher = Sha256::new();
        hasher.update(ops::encode_to_vec(&info)?);
        let hash = format!("{:x}", hasher.finalize());
        let directory = Path::new(CACHE_DIRECTORY).join(hash);

        Ok(Self { info, directory })
    }

    pub fn get_sandbox_directory(&self) -> PathBuf {
        self.directory.join(SANDBOX_DIRECTORY)
    }

    pub fn create_directory(&self) -> Result<()> {
        if self.directory.is_dir() {
            return Ok(());
        }
        if self.directory.exists() {
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

    pub fn load_data(&self) -> Result<Option<CacheData>> {
        let file = match File::open(self.directory.join(DATA_FILE)) {
            Ok(file) => file,
            Err(error) => match error.kind() {
                ErrorKind::NotFound => return Ok(None),
                _ => return Err(error.into()),
            },
        };
        let file_reader = BufReader::with_capacity(CHUNK_SIZE, file);
        let data = serde_json::from_reader(file_reader)?;
        Ok(Some(data))
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

    pub fn save_data(&self, data: &CacheData) -> Result<()> {
        let file = File::create(self.directory.join(DATA_FILE))?;
        let mut file_writer = BufWriter::with_capacity(CHUNK_SIZE, file);
        serde_json::to_writer_pretty(&mut file_writer, data)?;
        file_writer.flush()?;
        Ok(())
    }
}

#[derive(Debug, Encode, Serialize)]
struct CacheInfo<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    #[serde(with = "ops::serialize_byte_slice")]
    stdin: &'c [u8],
}

#[derive(Debug, Deserialize, Serialize)]
pub struct CacheData {
    pub exit_code: i32,
    #[serde(with = "ops::serialize_byte_vec")]
    pub stdout: Vec<u8>,
    #[serde(with = "ops::serialize_byte_vec")]
    pub stderr: Vec<u8>,
    pub read_dependencies: HashMap<PathBuf, DependencyKey>,
    pub write_outputs: HashSet<PathBuf>,
}

#[derive(Debug, Deserialize, Serialize)]
pub enum DependencyKey {
    DoesNotExist,
    Timestamp(u128),
    Hash(String),
}

fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
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
