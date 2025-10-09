use anyhow::{Result, ensure};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, ErrorKind};
use std::path::{Path, PathBuf};
use std::process::{Command as ShellCommand, Stdio};
use std::time::UNIX_EPOCH;

use crate::cache::{CacheCursor, CacheData, DependencyKey};
use crate::command::{ChildEnv, Command};
use crate::config::{EXCLUDED_PATHS, SKIP_COMMANDS, SKIP_SANDBOX_CONDITIONS, TRACE_FILE};
use crate::ops;

const PARSE_TRACE_SCRIPT: &str = include_str!("parse_trace.py");

pub(crate) fn skip_sandbox(command: &Command) -> bool {
    if SKIP_COMMANDS.contains(&command.name.as_str()) {
        return true;
    }
    for condition in SKIP_SANDBOX_CONDITIONS {
        if condition.name != command.name {
            continue;
        }
        for flag in condition.disallowed_flags {
            if command
                .arguments
                .iter()
                .any(|a| a == flag || a.starts_with(&format!("{flag}=")))
            {
                return false;
            }
        }
        return true;
    }
    false
}

pub(crate) fn check_cache_valid(cache: &CacheCursor<'_>, data: &CacheData) -> Result<bool> {
    if !check_read_dependencies(&data.read_dependencies)? {
        return Ok(false);
    }
    if !data.write_outputs.is_empty() && !cache.check_output_exists() {
        return Ok(false);
    }
    Ok(true)
}

pub(crate) fn parse_trace(env: &ChildEnv) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    #[derive(Clone, Copy, Debug, PartialEq)]
    enum ParseState {
        Start,
        ReadSet,
        WriteSet,
    }

    let trace_file = match env {
        ChildEnv::Sandbox(directory) => &directory.join("upperdir").join("tmp").join(TRACE_FILE),
        ChildEnv::TraceFile(file) => file,
    };
    let output = ShellCommand::new("python3")
        .args(["-c", PARSE_TRACE_SCRIPT, ops::path_to_string(&trace_file)?])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()?
        .wait_with_output()?;
    fs::remove_file(trace_file)?;

    let mut read_set = HashSet::new();
    let mut write_set = HashSet::new();
    let mut parse_state = ParseState::Start;
    let check_excluded = |path: &str| EXCLUDED_PATHS.iter().any(|e| path.starts_with(e));

    for line in String::from_utf8(output.stdout)?.lines() {
        let line = line.trim();
        match parse_state {
            ParseState::Start => {
                ensure!(line == "<read_set>");
                parse_state = ParseState::ReadSet;
            }
            ParseState::ReadSet => {
                if line == "<write_set>" {
                    parse_state = ParseState::WriteSet;
                    continue;
                }
                if !check_excluded(line) {
                    read_set.insert(PathBuf::from(line));
                }
            }
            ParseState::WriteSet => {
                if !check_excluded(line) {
                    write_set.insert(PathBuf::from(line));
                }
            }
        }
    }
    ensure!(parse_state == ParseState::WriteSet);

    Ok((read_set, write_set))
}

pub(crate) fn get_read_dependencies(
    read_set: HashSet<PathBuf>,
    write_set: &HashSet<PathBuf>,
) -> Result<HashMap<PathBuf, DependencyKey>> {
    let mut dependencies = HashMap::with_capacity(read_set.len());

    for path in read_set {
        if !path.exists() {
            dependencies.insert(path, DependencyKey::DoesNotExist);
            continue;
        }
        if !path.is_file() {
            continue;
        }

        if !write_set.contains(&path)
            && let Some(timestamp) = get_modified_timestamp(&path)?
        {
            dependencies.insert(path, DependencyKey::Timestamp(timestamp));
        } else if let Some(hash) = get_file_hash(&path)? {
            dependencies.insert(path, DependencyKey::Hash(hash));
        }
    }

    Ok(dependencies)
}

fn check_read_dependencies(dependencies: &HashMap<PathBuf, DependencyKey>) -> Result<bool> {
    for (path, key) in dependencies {
        match key {
            DependencyKey::DoesNotExist => {
                if path.exists() {
                    return Ok(false);
                }
            }
            DependencyKey::Timestamp(timestamp) => {
                if !path.is_file() {
                    return Ok(false);
                }
                let current_timestamp = get_modified_timestamp(path)?;
                if current_timestamp != Some(*timestamp) {
                    return Ok(false);
                }
            }
            DependencyKey::Hash(hash) => {
                if !path.is_file() {
                    return Ok(false);
                }
                let current_hash = get_file_hash(path)?;
                if current_hash.as_ref() != Some(hash) {
                    return Ok(false);
                }
            }
        }
    }
    Ok(true)
}

fn get_modified_timestamp(file_path: &Path) -> Result<Option<u128>> {
    let metadata = match fs::metadata(file_path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == ErrorKind::PermissionDenied => return Ok(None),
        Err(error) => return Err(error.into()),
    };
    let timestamp = metadata.modified()?.duration_since(UNIX_EPOCH)?.as_micros();
    Ok(Some(timestamp))
}

fn get_file_hash(file_path: &Path) -> Result<Option<String>> {
    let mut file = match File::open(file_path) {
        Ok(file) => file,
        Err(error) if error.kind() == ErrorKind::PermissionDenied => return Ok(None),
        Err(error) => return Err(error.into()),
    };

    let mut hasher = Sha256::new();
    io::copy(&mut file, &mut hasher)?;
    let hash = format!("{:x}", hasher.finalize());

    Ok(Some(hash))
}
