use anyhow::Result;
use bincode::{Decode, Encode};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::os::fd::AsRawFd;
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};
use std::sync::Arc;

use crate::cache::{self, CacheData};
use crate::command::Command;
use crate::config::{
    COMMIT_DIRECTORY, Config, DATA_FILE, DEBUG, OBSERVE_TRACE_FILE, OUTPUT_DIRECTORY, SANDBOX_DIRECTORY,
    STDERR_FILE, STDOUT_FILE, SUDO_SANDBOX, TRACE_FILE,
};
use crate::ops;

#[derive(Clone, Debug)]
pub(crate) struct CacheCursor<'c> {
    directory: PathBuf,
    try_command: String,
    observe: bool,
    debug_info: CacheInfo<'c>,
    _lease: Arc<CacheLease>,
}

/// Lock files live outside entries so replacing an entry cannot replace its lock.
/// Contention never blocks a live command (which may communicate with its peer).
#[derive(Debug)]
struct CacheLease {
    _lock: fs::File,
    transient: Option<PathBuf>,
}

impl Drop for CacheLease {
    fn drop(&mut self) {
        if let Some(path) = &self.transient {
            let _ = fs::remove_dir_all(path);
        }
    }
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
            version: 12,
            observe: config.observe_command.is_some(),
            full_tracing: config.full_tracing,
            umask: fs::read_to_string("/proc/self/status")?
                .lines()
                .find_map(|line| line.strip_prefix("Umask:"))
                .unwrap_or("")
                .trim()
                .to_owned(),
            command_hash: command.hash,
            stdin_hash,
        })?;
        let hash = ops::data::hash_bytes(&key_data);
        let lock_directory = config.cache_directory.join("locks");
        fs::create_dir_all(&lock_directory)?;
        let lock = fs::OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(lock_directory.join(format!("batch_{hash}.lock")))?;
        let locked = unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } == 0;
        let transient = if locked {
            None
        } else {
            let error = std::io::Error::last_os_error();
            if error.raw_os_error() != Some(libc::EWOULDBLOCK) {
                return Err(error.into());
            }
            Some(
                config
                    .cache_directory
                    .join(format!("uncached_{}", rand::random::<u128>())),
            )
        };
        let directory = transient
            .clone()
            .unwrap_or_else(|| config.cache_directory.join(format!("batch_{hash}")));
        Ok(Self {
            directory,
            _lease: Arc::new(CacheLease {
                _lock: lock,
                transient,
            }),
            try_command: config.try_command.clone(),
            observe: config.observe_command.is_some(),
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

    pub(crate) fn get_observe_trace_file(&self) -> PathBuf {
        self.directory.join(OBSERVE_TRACE_FILE)
    }

    pub(crate) fn data_outputs_exist(&self) -> bool {
        self.get_stdout_file().is_file() && self.get_stderr_file().is_file()
    }

    pub(crate) fn file_outputs_exist(&self) -> bool {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        if self.observe {
            cache::effects::valid(&output_directory)
        } else {
            output_directory.is_dir()
        }
    }

    pub(crate) fn create_directory(&self) -> Result<()> {
        let debug_info = if DEBUG { Some(&self.debug_info) } else { None };
        cache::create_directory(&self.directory, debug_info)
    }

    pub(crate) fn extract_sandbox_output(&self) -> Result<()> {
        let sandbox_directory = self.directory.join(SANDBOX_DIRECTORY);
        self.extract_sandbox_output_from(&sandbox_directory)
    }

    /// Materializes sandbox outputs from an arbitrary runtime sandbox into this cache entry.
    /// This is used by the streaming executor because its temporary sandbox may be a mounted
    /// tmpfs inside Docker and therefore cannot be renamed into the cache directory.
    pub(crate) fn extract_sandbox_output_from(&self, sandbox_directory: &Path) -> Result<()> {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        let ignore_source = sandbox_directory.join("ignore");
        let ignore_destination = output_directory.join("ignore");

        fs::create_dir_all(&output_directory)?;
        move_or_copy_path(
            &sandbox_directory.join("upperdir"),
            &output_directory.join("upperdir"),
        )?;
        if ignore_source.exists() {
            move_or_copy_path(&ignore_source, &ignore_destination)?;
        } else {
            fs::write(&ignore_destination, b"")?;
        }
        let _ = remove_sandbox(sandbox_directory);

        Ok(())
    }

    pub(crate) fn capture_observe_output(&self, write_set: &HashSet<PathBuf>) -> Result<()> {
        cache::effects::capture(&self.directory.join(OUTPUT_DIRECTORY), write_set)
    }

    pub(crate) fn commit_output(&self) -> Result<()> {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        if cache::effects::exists(&output_directory) {
            return cache::effects::replay(&output_directory);
        }
        let commit_directory = self.directory.join(COMMIT_DIRECTORY);

        let copy_status = ShellCommand::new("cp")
            .args([
                "-rp",
                ops::file::path_to_string(&output_directory)?,
                ops::file::path_to_string(&commit_directory)?,
            ])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        if !copy_status.success() {
            anyhow::bail!("cache output copy failed: {copy_status}");
        }
        let commit_status = ShellCommand::new(&self.try_command)
            .args(["commit", ops::file::path_to_string(&commit_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        if !commit_status.success() {
            anyhow::bail!("cache output commit failed: {commit_status}");
        }
        fs::remove_dir_all(&commit_directory)?;

        Ok(())
    }

    pub(crate) fn clean(&self) -> Result<()> {
        let data_file = ops::file::add_data_extension(DATA_FILE.to_owned());
        ops::file::remove_file(&self.directory.join(&data_file))?;
        ops::file::remove_directory(&self.directory.join(OUTPUT_DIRECTORY))?;
        ops::file::remove_directory(&self.directory.join(COMMIT_DIRECTORY))?;
        remove_sandbox(&self.get_sandbox_directory())?;
        Ok(())
    }

    pub(crate) fn load_data(&self) -> Result<Option<CacheData>> {
        let Some(entry): Option<CachedEntry> =
            ops::data::decode_from_file(&self.directory, DATA_FILE.to_owned())?
        else {
            return Ok(None);
        };
        if self.output_hashes().ok() != Some(entry.output_hashes) {
            return Ok(None);
        }
        Ok(Some(entry.data))
    }

    fn output_hashes(&self) -> Result<[u64; 2]> {
        let mut hashes = [0; 2];
        for (hash, path) in hashes
            .iter_mut()
            .zip([self.get_stdout_file(), self.get_stderr_file()])
        {
            if !fs::symlink_metadata(&path)?.is_file() {
                anyhow::bail!("cached stream is not a regular file");
            }
            *hash = ops::data::hash_stream(&mut fs::File::open(path)?)?;
        }
        Ok(hashes)
    }

    pub(crate) fn save_data(&self, data: &CacheData) -> Result<()> {
        let entry = CachedEntry {
            data: data.clone(),
            output_hashes: self.output_hashes()?,
        };
        ops::data::encode_to_file(&entry, &self.directory, DATA_FILE.to_owned())
    }
}

// Hash the stored representation (including compression), before replay emits
// bytes or filesystem effects. Missing/truncated/corrupt streams are cache misses.
#[derive(Decode, Deserialize, Encode, Serialize)]
struct CachedEntry {
    data: CacheData,
    output_hashes: [u64; 2],
}

#[derive(Clone, Debug, Serialize)]
struct CacheInfo<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    stdin_hash: u64,
    #[serde(with = "ops::serialize_bytes")]
    stdin: Option<&'c [u8]>,
}

#[derive(Clone, Debug, Encode)]
struct CacheKey {
    version: u32,
    observe: bool,
    full_tracing: bool,
    umask: String,
    command_hash: u64,
    stdin_hash: u64,
}

pub(crate) fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
        if !sandbox_directory.exists() {
            return Ok(());
        }
        unmount_sandbox_if_needed(sandbox_directory)?;
        let status = ShellCommand::new("sudo")
            .args(["-n", "rm", "-rf", ops::file::path_to_string(sandbox_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        if !status.success() {
            return Err(anyhow::anyhow!(
                "failed removing sandbox: {}",
                sandbox_directory.display()
            ));
        }
    } else {
        ops::file::remove_directory(sandbox_directory)?;
    }
    Ok(())
}

fn unmount_sandbox_if_needed(sandbox_directory: &Path) -> Result<()> {
    let sandbox = ops::file::path_to_string(sandbox_directory)?;
    let findmnt_status = ShellCommand::new("findmnt")
        .args(["-n", sandbox])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?
        .wait()?;

    if !findmnt_status.success() {
        return Ok(());
    }

    let status = ShellCommand::new("sudo")
        .args(["-n", "umount", "-l", sandbox])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?
        .wait()?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow::anyhow!(
            "failed unmounting sandbox: {}",
            sandbox_directory.display()
        ))
    }
}

fn move_or_copy_path(source: &Path, destination: &Path) -> Result<()> {
    if destination.is_dir() {
        fs::remove_dir_all(destination)?;
    } else if destination.exists() {
        fs::remove_file(destination)?;
    }

    match fs::rename(source, destination) {
        Ok(()) => Ok(()),
        Err(error) if matches!(error.raw_os_error(), Some(16 | 18)) => {
            copy_path(source, destination)?;
            if source.is_dir() {
                fs::remove_dir_all(source)?;
            } else if source.exists() {
                fs::remove_file(source)?;
            }
            Ok(())
        }
        Err(error) => Err(error.into()),
    }
}

fn copy_path(source: &Path, destination: &Path) -> Result<()> {
    if source.is_file() {
        fs::copy(source, destination)?;
        return Ok(());
    }

    let status = ShellCommand::new("cp")
        .args([
            "-a",
            ops::file::path_to_string(source)?,
            ops::file::path_to_string(destination)?,
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?
        .wait()?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow::anyhow!(
            "copy failed: {} -> {}",
            source.display(),
            destination.display()
        ))
    }
}
