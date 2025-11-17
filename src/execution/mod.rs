pub(crate) mod batch_executor;
pub(crate) mod chunk_executor;
pub(crate) mod skip_executor;
pub(crate) mod stream_executor;

use anyhow::{Result, anyhow, ensure};
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, BufReader, ErrorKind, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::UNIX_EPOCH;
use zstd::Decoder;

use crate::annotation;
use crate::cache::batch_cache::{CacheCursor, CacheData, DependencyKey};
use crate::command::{Command, Runtime, RuntimeType};
use crate::config::{
    BUFFER_SIZE, Config, DYNAMIC_EXCLUDED_PATHS, EXCLUDED_PATHS, INTROSPECT_DIRECTORY, PARALLEL_SIZE,
    TRACE_FILE, TraceType,
};
use crate::ops;
use crate::scripts;

pub(crate) fn get_trace_type(cache_directory: &Path, command: &Command) -> TraceType {
    if annotation::check_pure(command) {
        return TraceType::Nothing;
    } else if annotation::check_stateless(command) || annotation::check_read_only(command) {
        return TraceType::TraceFile;
    }

    let introspect_file = cache_directory
        .join(INTROSPECT_DIRECTORY)
        .join(format!("command_{}.incr", command.hash));
    if introspect_file.exists() {
        return TraceType::TraceFile;
    }

    TraceType::Sandbox
}

pub(crate) fn parse_trace(runtime: &Runtime) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    let trace_file = match &runtime.typ {
        RuntimeType::Sandbox(directory) => &directory.join("upperdir").join("tmp").join(TRACE_FILE),
        RuntimeType::TraceFile(file) => file,
        RuntimeType::Nothing => return Ok((HashSet::new(), HashSet::new())),
    };
    let (mut read_set, mut write_set) = scripts::parse_trace(trace_file).unwrap();
    fs::remove_file(trace_file)?;

    read_set.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::files::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });
    write_set.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::files::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });

    Ok((read_set, write_set))
}

pub(crate) fn check_cache_valid(cache: &CacheCursor<'_>, data: &CacheData) -> Result<bool> {
    if !cache.data_outputs_exist() || !check_read_dependencies(&data.read_dependencies)? {
        return Ok(false);
    }
    if !data.write_outputs.is_empty() && !cache.file_outputs_exist() {
        return Ok(false);
    }
    Ok(true)
}

pub(crate) fn get_read_dependencies(
    read_set: &HashSet<PathBuf>,
    write_set: &HashSet<PathBuf>,
) -> Result<HashMap<PathBuf, DependencyKey>> {
    let paths = read_set.iter().collect::<Vec<_>>();
    let results = parallel_process(&paths, |chunk| {
        let mut dependencies = Vec::with_capacity(chunk.len());
        for &path in chunk {
            if !path.exists() {
                dependencies.push((path.clone(), DependencyKey::DoesNotExist));
                continue;
            }
            if !path.is_file() {
                continue;
            }
            if !write_set.contains(path) {
                if let Some(timestamp) = get_modified_timestamp(path)? {
                    dependencies.push((path.clone(), DependencyKey::Timestamp(timestamp)));
                }
            } else if let Some(hash) = get_file_hash(path)? {
                dependencies.push((path.clone(), DependencyKey::Hash(hash)));
            }
        }
        Ok(dependencies)
    })?;

    let mut dependencies = HashMap::with_capacity(read_set.len());
    for chunk in results {
        dependencies.extend(chunk);
    }

    Ok(dependencies)
}

pub(crate) fn filter_dependencies(
    read_dependencies: &mut HashMap<PathBuf, DependencyKey>,
    write_set: &mut HashSet<PathBuf>,
) -> Result<()> {
    let removed = read_dependencies
        .iter()
        .filter_map(|(p, k)| {
            let excluded = DYNAMIC_EXCLUDED_PATHS.iter().any(|e| {
                ops::files::path_to_string(p)
                    .map(|p| p.starts_with(e))
                    .unwrap_or(false)
            });
            if excluded && k == &mut DependencyKey::DoesNotExist && !p.exists() {
                Some(p.clone())
            } else {
                None
            }
        })
        .collect::<Vec<_>>();
    for path in &removed {
        read_dependencies.remove(path);
        write_set.remove(path);
    }
    Ok(())
}

fn check_read_dependencies(dependencies: &HashMap<PathBuf, DependencyKey>) -> Result<bool> {
    let dependencies = dependencies.iter().collect::<Vec<_>>();
    let results = parallel_process(&dependencies, |chunk| {
        for (path, key) in chunk {
            match key {
                DependencyKey::DoesNotExist => {
                    if path.exists() {
                        return Ok(false);
                    }
                }
                DependencyKey::Timestamp(timestamp) => {
                    if !path.is_file() || get_modified_timestamp(path)? != Some(*timestamp) {
                        return Ok(false);
                    }
                }
                DependencyKey::Hash(hash) => {
                    if !path.is_file() || get_file_hash(path)? != Some(*hash) {
                        return Ok(false);
                    }
                }
            }
        }
        Ok(true)
    })?;
    Ok(results.into_iter().all(|r| r))
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
    let mut file_reader = BufReader::with_capacity(BUFFER_SIZE, file);
    Ok(Some(ops::data::hash_stream(&mut file_reader)?))
}

fn parallel_process<T, F, O>(data: &[T], function: F) -> Result<Vec<O>>
where
    T: Sync,
    F: Fn(&[T]) -> Result<O> + Sync,
    O: Send,
{
    let num_chunks = data.len().div_ceil(PARALLEL_SIZE);
    if num_chunks <= 1 {
        return Ok(vec![function(data)?]);
    }

    thread::scope(|scope| {
        let mut threads = Vec::with_capacity(num_chunks);
        let mut results = Vec::with_capacity(num_chunks);
        for chunk in data.chunks(PARALLEL_SIZE) {
            threads.push(scope.spawn(|| function(chunk)));
        }
        for thread in threads {
            results.push(thread.join().map_err(|e| anyhow!("{e:?}"))??);
        }
        Ok(results)
    })
}

pub(crate) fn output_data<D>(
    data_file: &Path,
    start_index: usize,
    destination: &mut D,
    compressed: bool,
) -> Result<bool>
where
    D: Write,
{
    let mut file = File::open(data_file)?;
    if !compressed {
        let length = file.metadata()?.len() as usize;
        ensure!(start_index <= length);
        if start_index == length {
            return Ok(true);
        }
    }

    if !compressed {
        file.seek(SeekFrom::Start(start_index as u64))?;
        let mut file_reader = BufReader::with_capacity(BUFFER_SIZE, file);
        output_from_stream(&mut file_reader, destination)
    } else {
        let mut compressed_reader = Decoder::new(BufReader::with_capacity(BUFFER_SIZE, file))?;
        io::copy(
            &mut (&mut compressed_reader).take(start_index as u64),
            &mut io::sink(),
        )?;
        output_from_stream(&mut compressed_reader, destination)
    }
}

fn output_from_stream<S, D>(source: &mut S, destination: &mut D) -> Result<bool>
where
    S: Read,
    D: Write,
{
    match io::copy(source, destination) {
        Ok(_) => {
            destination.flush()?;
            Ok(true)
        }
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(false),
        Err(error) => Err(error.into()),
    }
}

pub(crate) fn save_introspection(config: &Config, command: &Command, cache_data: &CacheData) -> Result<()> {
    let introspect_directory = config.cache_directory.join(INTROSPECT_DIRECTORY);
    let introspect_file = introspect_directory.join(format!("command_{}.incr", command.hash));
    fs::create_dir_all(&introspect_directory)?;
    if cache_data.write_outputs.is_empty() {
        File::create(&introspect_file)?;
    } else if introspect_file.exists() {
        ops::files::remove_file(&introspect_file)?;
    }
    Ok(())
}
