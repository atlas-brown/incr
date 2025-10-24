pub(crate) mod batch_executor;
pub(crate) mod skip_executor;
pub(crate) mod stream_executor;

use anyhow::{Result, ensure};
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, BufReader, ErrorKind, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

use crate::cache::{CacheCursor, CacheData, DependencyKey};
use crate::command::{ChildEnv, Command, EnvType};
use crate::config::{
    CHUNK_SIZE, EXCLUDED_PATHS, IGNORE_COMMANDS, SKIP_CACHE_CONDITIONS, SKIP_COMMANDS,
    SKIP_SANDBOX_CONDITIONS, SKIP_TRACE_CONDITIONS, SkipCondition, TRACE_FILE, TraceType,
};
use crate::ops;
use crate::scripts;

pub(crate) fn skip_command(command: &Command, environment: &HashMap<String, String>) -> bool {
    IGNORE_COMMANDS.contains(&command.name.as_str())
        || SKIP_COMMANDS.contains(&command.name.as_str())
        || environment.contains_key(&format!("BASH_FUNC_{}%%", command.name))
}

pub(crate) fn get_trace_type(command: &Command) -> TraceType {
    if IGNORE_COMMANDS.contains(&command.name.as_str()) || SKIP_COMMANDS.contains(&command.name.as_str()) {
        return TraceType::Nothing;
    }

    let (flags, values) = parse_arguments(&command.arguments);
    if SKIP_TRACE_CONDITIONS
        .iter()
        .any(|c| check_condition(c, command, &flags, &values, 0))
    {
        return TraceType::Nothing;
    }
    if SKIP_SANDBOX_CONDITIONS
        .iter()
        .any(|c| check_condition(c, command, &flags, &values, 0))
    {
        return TraceType::TraceFile;
    }

    TraceType::Sandbox
}

pub(crate) fn skip_cache(command: &Command, stdin_length: usize) -> bool {
    if IGNORE_COMMANDS.contains(&command.name.as_str()) || SKIP_COMMANDS.contains(&command.name.as_str()) {
        return true;
    }
    let (flags, values) = parse_arguments(&command.arguments);
    SKIP_CACHE_CONDITIONS
        .iter()
        .any(|c| check_condition(c, command, &flags, &values, stdin_length))
}

fn parse_arguments(arguments: &[String]) -> (HashSet<String>, Vec<String>) {
    let mut flags = HashSet::new();
    let mut values = Vec::new();
    for argument in arguments {
        if argument.starts_with("--") && argument.len() >= 3 {
            match argument.find("=") {
                Some(index) => flags.insert(argument[2..index].to_lowercase()),
                None => flags.insert(argument[2..].to_lowercase()),
            };
        } else if !argument.starts_with("--") && argument.starts_with("-") && argument.len() >= 2 {
            if argument.len() >= 3 && &argument[2..3] == "=" {
                flags.insert(argument[1..2].to_lowercase());
            } else {
                for f in 1..argument.len() {
                    flags.insert(argument[f..f + 1].to_lowercase());
                }
            }
        } else {
            values.push(argument.clone());
        }
    }
    (flags, values)
}

fn check_condition(
    condition: &SkipCondition,
    command: &Command,
    flags: &HashSet<String>,
    values: &[String],
    stdin_length: usize,
) -> bool {
    condition.name == command.name
        && !condition.disallowed_flags.iter().any(|&f| flags.contains(f))
        && values.len() <= condition.max_arguments
        && stdin_length <= condition.max_input
}

pub(crate) fn check_cache_valid(cache: &CacheCursor<'_>, data: &CacheData) -> Result<bool> {
    if !check_read_dependencies(&data.read_dependencies)? || !cache.data_outputs_exist() {
        return Ok(false);
    }
    if !data.write_outputs.is_empty() && !cache.file_outputs_exist() {
        return Ok(false);
    }
    Ok(true)
}

pub(crate) fn parse_trace(child_env: &ChildEnv) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    let trace_file = match &child_env.typ {
        EnvType::Sandbox(directory) => &directory.join("upperdir").join("tmp").join(TRACE_FILE),
        EnvType::TraceFile(file) => file,
        EnvType::Nothing => return Ok((HashSet::new(), HashSet::new())),
    };
    let (mut read_set, mut write_set) = scripts::parse_trace(trace_file).unwrap();
    fs::remove_file(trace_file)?;

    read_set.retain(|p| {
        !EXCLUDED_PATHS
            .iter()
            .any(|e| ops::path_to_string(p).map(|p| p.starts_with(e)).unwrap_or(true))
    });
    write_set.retain(|p| {
        !EXCLUDED_PATHS
            .iter()
            .any(|e| ops::path_to_string(p).map(|p| p.starts_with(e)).unwrap_or(true))
    });

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
                if current_hash != Some(*hash) {
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

fn get_file_hash(file_path: &Path) -> Result<Option<u64>> {
    let file = match File::open(file_path) {
        Ok(file) => file,
        Err(error) if error.kind() == ErrorKind::PermissionDenied => return Ok(None),
        Err(error) => return Err(error.into()),
    };
    let mut file_reader = BufReader::with_capacity(CHUNK_SIZE, file);
    Ok(Some(ops::hash_stream(&mut file_reader)?))
}

pub(crate) fn output_data<D>(data_file: &Path, start: usize, destination: &mut D) -> Result<bool>
where
    D: Write,
{
    let mut file = File::open(data_file)?;
    let length = file.metadata()?.len() as usize;
    ensure!(start <= length);
    if start == length {
        return Ok(true);
    }

    file.seek(SeekFrom::Start(start as u64))?;
    let mut file_reader = BufReader::with_capacity(CHUNK_SIZE, file);
    match io::copy(&mut file_reader, destination) {
        Ok(count) => {
            ensure!(count as usize == length - start);
            destination.flush()?;
            Ok(true)
        }
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(false),
        Err(error) => Err(error.into()),
    }
}
