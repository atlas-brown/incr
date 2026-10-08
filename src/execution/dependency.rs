use anyhow::Result;
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufReader, ErrorKind};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

use crate::cache::batch_cache::CacheCursor;
use crate::cache::{CacheData, DependencyKey};
use crate::command::Command;
use crate::config::{BUFFER_SIZE, Config, DYNAMIC_EXCLUDED_PATHS, INTROSPECT_DIRECTORY};
use crate::ops;

pub(crate) fn check_cache_valid(cache: &CacheCursor<'_>, data: &CacheData) -> Result<bool> {
    if !data.replay_barriers.is_empty()
        || !cache.data_outputs_exist()
        || !check_read_dependencies(&data.read_dependencies)?
    {
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
    let results = ops::thread::parallel_process(&paths, |chunk| {
        let mut dependencies = Vec::with_capacity(chunk.len());
        for &path in chunk {
            let key =
                capture_dependency(path, write_set.contains(path)).unwrap_or(DependencyKey::Uncacheable);
            dependencies.push((path.clone(), key));
        }
        Ok(dependencies)
    })?;

    let mut dependencies = HashMap::with_capacity(read_set.len());
    for chunk in results {
        dependencies.extend(chunk);
    }

    Ok(dependencies)
}

fn capture_dependency(path: &Path, written: bool) -> Result<DependencyKey> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == ErrorKind::NotFound => return Ok(DependencyKey::DoesNotExist),
        Err(error) => return Err(error.into()),
    };
    let modified = metadata.modified()?.duration_since(UNIX_EPOCH)?.as_nanos();
    let changed_sec = metadata.ctime();
    let changed_nsec = metadata.ctime_nsec();
    let mode = metadata.mode();
    Ok(if metadata.is_symlink() {
        DependencyKey::SymlinkState {
            target: fs::read_link(path)?,
            modified,
            changed_sec,
            changed_nsec,
            mode,
        }
    } else if metadata.is_dir() {
        DependencyKey::DirectoryState {
            modified,
            changed_sec,
            changed_nsec,
            mode,
        }
    } else if metadata.is_file() {
        let state = DependencyKey::FileState {
            modified,
            changed_sec,
            changed_nsec,
            size: metadata.len(),
            mode,
        };
        if written {
            match get_file_hash(path)? {
                Some(hash) => DependencyKey::All(vec![state, DependencyKey::Hash(hash)]),
                None => DependencyKey::Uncacheable,
            }
        } else {
            state
        }
    } else {
        DependencyKey::Uncacheable
    })
}

pub(crate) fn filter_dependencies(
    read_dependencies: &mut HashMap<PathBuf, DependencyKey>,
    write_set: &mut HashSet<PathBuf>,
) -> Result<()> {
    let removed = read_dependencies
        .iter()
        .filter_map(|(path, key)| {
            let excluded = DYNAMIC_EXCLUDED_PATHS
                .iter()
                .any(|excluded| path.starts_with(excluded));
            if excluded && key == &DependencyKey::DoesNotExist && !path.exists() {
                Some(path.clone())
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
    let results = ops::thread::parallel_process(&dependencies, |chunk| {
        for (path, key) in chunk {
            // Files can disappear or become unreadable between probes. That is
            // a cache miss, not an error in the user's command.
            if !check_dependency(path, key).unwrap_or(false) {
                return Ok(false);
            }
        }
        Ok(true)
    })?;
    Ok(results.into_iter().all(|valid| valid))
}

fn check_dependency(path: &Path, key: &DependencyKey) -> Result<bool> {
    Ok(match key {
        DependencyKey::Uncacheable => false,
        DependencyKey::ParentDirectory {
            mode,
            uid,
            gid,
            access,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            metadata.is_dir()
                && metadata.mode() == *mode
                && metadata.uid() == *uid
                && metadata.gid() == *gid
                && crate::ops::permissions::effective_access(path)? == *access
        }
        DependencyKey::All(keys) => {
            for key in keys {
                if !check_dependency(path, key)? {
                    return Ok(false);
                }
            }
            true
        }
        DependencyKey::FileState {
            modified,
            changed_sec,
            changed_nsec,
            size,
            mode,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            metadata.is_file()
                && metadata.len() == *size
                && metadata.mode() == *mode
                && metadata.ctime() == *changed_sec
                && metadata.ctime_nsec() == *changed_nsec
                && metadata.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() == *modified
        }
        DependencyKey::DirectoryState {
            modified,
            changed_sec,
            changed_nsec,
            mode,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            metadata.is_dir()
                && metadata.mode() == *mode
                && metadata.ctime() == *changed_sec
                && metadata.ctime_nsec() == *changed_nsec
                && metadata.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() == *modified
        }
        DependencyKey::SymlinkState {
            target,
            modified,
            changed_sec,
            changed_nsec,
            mode,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            metadata.file_type().is_symlink()
                && metadata.mode() == *mode
                && metadata.ctime() == *changed_sec
                && metadata.ctime_nsec() == *changed_nsec
                && metadata.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() == *modified
                && fs::read_link(path)? == *target
        }
        DependencyKey::DoesNotExist => matches!(fs::symlink_metadata(path),
            Err(error) if error.kind() == ErrorKind::NotFound),
        DependencyKey::Hash(hash) => path.is_file() && get_file_hash(path)? == Some(*hash),
    })
}

fn get_file_hash(file_path: &Path) -> Result<Option<u64>> {
    let file = match fs::OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NONBLOCK)
        .open(file_path)
    {
        Ok(file) => file,
        Err(error) if error.kind() == ErrorKind::PermissionDenied => return Ok(None),
        Err(error) => return Err(error.into()),
    };
    if !file.metadata()?.is_file() {
        return Ok(None);
    }
    let mut file_reader = BufReader::with_capacity(BUFFER_SIZE, file);
    Ok(Some(ops::data::hash_stream(&mut file_reader)?))
}

pub(crate) fn save_introspection(config: &Config, command: &Command, cache_data: &CacheData) -> Result<()> {
    if config.skip_introspection {
        return Ok(());
    }

    let introspect_file = get_introspect_file(&config.cache_directory, command.hash);
    if let Some(parent) = introspect_file.parent() {
        fs::create_dir_all(parent)?;
    }
    if cache_data.write_outputs.is_empty() {
        File::create(&introspect_file)?;
    } else if introspect_file.exists() {
        ops::file::remove_file(&introspect_file)?;
    }

    Ok(())
}

pub(crate) fn get_introspect_file(cache_directory: &Path, command_hash: u64) -> PathBuf {
    cache_directory
        .join(INTROSPECT_DIRECTORY)
        .join(format!("command_{command_hash}.incr"))
}
