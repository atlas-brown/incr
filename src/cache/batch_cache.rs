use anyhow::Result;
use bincode::Encode;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};

use crate::cache::{self, CacheData};
use crate::command::Command;
use crate::config::{
    COMMIT_DIRECTORY, Config, DATA_FILE, DEBUG, OUTPUT_DIRECTORY, SANDBOX_DIRECTORY, STDERR_FILE,
    STDOUT_FILE, SUDO_SANDBOX, TRACE_FILE,
};
use crate::ops;

/// Handle to a `batch_<hash>` cache directory. Provides access to cached stdout/stderr,
/// sandbox overlay, trace file, and serialized [`CacheData`]. The hash is derived from
/// (command name, arguments, environment, stdin hash).
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
            directory: config.cache_directory.join(format!("batch_{hash}")),
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

    pub(crate) fn data_outputs_exist(&self) -> bool {
        self.get_stdout_file().is_file() && self.get_stderr_file().is_file()
    }

    pub(crate) fn file_outputs_exist(&self) -> bool {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
        output_directory.is_dir()
    }

    pub(crate) fn create_directory(&self) -> Result<()> {
        let debug_info = if DEBUG { Some(&self.debug_info) } else { None };
        cache::create_directory(&self.directory, debug_info)
    }

    /// Moves the OverlayFS upper layer out of the sandbox into the outputs directory
    /// and removes the remaining sandbox files.
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
        let _ = remove_sandbox(&sandbox_directory);

        Ok(())
    }

    /// Applies cached file outputs to the real filesystem via `try.sh commit`.
    pub(crate) fn commit_output(&self) -> Result<()> {
        let output_directory = self.directory.join(OUTPUT_DIRECTORY);
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
            return Err(anyhow::anyhow!(
                "copy failed: {} -> {}",
                output_directory.display(),
                commit_directory.display()
            ));
        }
        ShellCommand::new(&self.try_command)
            .args(["commit", ops::file::path_to_string(&commit_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        fs::remove_dir_all(&commit_directory)?;

        Ok(())
    }

    pub(crate) fn clean(&self) -> Result<()> {
        let data_file = ops::file::add_data_extension(DATA_FILE.to_owned());
        ops::file::remove_file(Path::new(&data_file))?;
        ops::file::remove_directory(&self.directory.join(OUTPUT_DIRECTORY))?;
        ops::file::remove_directory(&self.directory.join(COMMIT_DIRECTORY))?;
        remove_sandbox(&self.get_sandbox_directory())?;
        Ok(())
    }

    pub(crate) fn load_data(&self) -> Result<Option<CacheData>> {
        ops::data::decode_from_file(&self.directory, DATA_FILE.to_owned())
    }

    pub(crate) fn save_data(&self, data: &CacheData) -> Result<()> {
        ops::data::encode_to_file(data, &self.directory, DATA_FILE.to_owned())
    }
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
struct CacheKey<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    stdin_hash: u64,
}

/// Removes a sandbox directory. Uses `sudo rm -rf` when [`SUDO_SANDBOX`] is true,
/// since OverlayFS mounts may create root-owned files.
pub(crate) fn remove_sandbox(sandbox_directory: &Path) -> Result<()> {
    if SUDO_SANDBOX {
        if !sandbox_directory.exists() {
            return Ok(());
        }
        unmount_sandbox_if_needed(sandbox_directory)?;
        let status = ShellCommand::new("sudo")
            .args(["rm", "-rf", ops::file::path_to_string(sandbox_directory)?])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?
            .wait()?;
        if !status.success() {
            return Err(anyhow::anyhow!("failed removing sandbox: {}", sandbox_directory.display()));
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
        .args(["umount", "-l", sandbox])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?
        .wait()?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow::anyhow!("failed unmounting sandbox: {}", sandbox_directory.display()))
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
