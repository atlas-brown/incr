use anyhow::{Result, anyhow, ensure};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::env;
use std::fs::{self, File};
use std::io::{self, ErrorKind, Read, Write};
use std::mem;
use std::path::{Path, PathBuf};
use std::process::{Child, Command as ShellCommand, Stdio};
use std::time::UNIX_EPOCH;

use crate::cache::DependencyKey;
use crate::config::{
    CHUNK_SIZE, EXCLUDED_PATHS, EXCLUDED_VARS, STRACE_COMMAND, TRACE_FILE, TRY_COMMAND,
};
use crate::ops;

const PARSE_TRACE_SCRIPT: &str = include_str!("parse_trace.py");

#[derive(Debug)]
pub struct Command {
    pub name: String,
    pub arguments: Vec<String>,
    pub environment: BTreeMap<String, String>,
}

pub fn get_command() -> Result<Option<Command>> {
    let mut arguments = env::args().collect::<Vec<String>>();
    if arguments.len() <= 1 {
        return Ok(None);
    }

    if arguments.len() == 2 {
        let command_string = mem::take(&mut arguments[1]);
        arguments = shlex::split(&command_string).ok_or(anyhow!("Could not split command"))?
    } else {
        arguments.remove(0);
    };
    let name = arguments.remove(0);

    let excluded_vars = EXCLUDED_VARS.iter().copied().collect::<HashSet<_>>();
    let mut environment = BTreeMap::new();
    for (var, value) in env::vars() {
        if !excluded_vars.contains(var.as_str()) {
            environment.insert(var, value);
        }
    }

    Ok(Some(Command {
        name,
        arguments,
        environment,
    }))
}

pub fn spawn_command(command: &Command, sandbox_directory: &Path) -> Result<Child> {
    let mut command_parts = Vec::with_capacity(command.arguments.len() + 1);
    command_parts.push(command.name.as_str());
    command_parts.extend(command.arguments.iter().map(|a| a.as_str()));
    let command_string = shlex::try_join(command_parts)?;

    let arguments = &[
        "-D",
        ops::path_to_string(sandbox_directory)?,
        STRACE_COMMAND,
        "-yf",
        "--seccomp-bpf",
        "--trace=fork,clone,%file",
        "-o",
        &format!("/tmp/{TRACE_FILE}"),
        "bash",
        "-c",
        &shlex::try_quote(&command_string)?,
    ];

    fs::create_dir_all(sandbox_directory)?;
    ShellCommand::new(TRY_COMMAND)
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.into())
}

pub fn capture_stream<S, D>(mut source: S, mut destination: D) -> Result<Vec<u8>>
where
    S: Read,
    D: Write,
{
    let mut data = Vec::new();
    let mut chunk = [0; CHUNK_SIZE];
    loop {
        let count = source.read(&mut chunk)?;
        if count == 0 {
            break;
        }
        destination.write_all(&chunk[..count])?;
        destination.flush()?;
        data.extend_from_slice(&chunk[..count]);
    }
    Ok(data)
}

pub fn parse_trace(sandbox_directory: &Path) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    #[derive(Debug, PartialEq)]
    enum ParseState {
        Start,
        ReadSet,
        WriteSet,
    }

    let trace_file = sandbox_directory
        .join("upperdir")
        .join("tmp")
        .join(TRACE_FILE);
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

pub fn get_read_dependencies(
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

pub fn check_read_dependencies(dependencies: &HashMap<PathBuf, DependencyKey>) -> Result<bool> {
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
        Err(error) => match error.kind() {
            ErrorKind::PermissionDenied => return Ok(None),
            _ => return Err(error.into()),
        },
    };
    let timestamp = metadata.modified()?.duration_since(UNIX_EPOCH)?.as_micros();
    Ok(Some(timestamp))
}

fn get_file_hash(file_path: &Path) -> Result<Option<String>> {
    let mut file = match File::open(file_path) {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::PermissionDenied => return Ok(None),
            _ => return Err(error.into()),
        },
    };

    let mut hasher = Sha256::new();
    io::copy(&mut file, &mut hasher)?;
    let hash = format!("{:x}", hasher.finalize());

    Ok(Some(hash))
}
