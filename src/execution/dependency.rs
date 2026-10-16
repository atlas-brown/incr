use anyhow::Result;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::{BufReader, ErrorKind};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

use crate::cache::batch_cache::CacheCursor;
use crate::cache::{CacheData, DependencyKey};
use crate::config::{BUFFER_SIZE, DYNAMIC_EXCLUDED_PATHS};
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
        Err(error) if error.kind() == ErrorKind::NotADirectory => return Ok(DependencyKey::NotDirectory),
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
                ops::profile::event(|| {
                    serde_json::json!({
                        "kind": "dependency_miss", "path": path, "expected": key,
                    })
                });
                return Ok(false);
            }
        }
        Ok(true)
    })?;
    Ok(results.into_iter().all(|valid| valid))
}

pub(crate) fn capture_produced_file(path: &Path) -> Result<crate::cache::ProducedFile> {
    let metadata = fs::symlink_metadata(path)?;
    anyhow::ensure!(metadata.is_file(), "overwrite did not produce a regular file");
    Ok(crate::cache::ProducedFile {
        device: metadata.dev(),
        inode: metadata.ino(),
        size: metadata.len(),
        mode: metadata.mode(),
        uid: metadata.uid(),
        gid: metadata.gid(),
        links: metadata.nlink(),
        access: crate::ops::permissions::effective_access(path)?,
        hash: get_file_hash(path)?.ok_or_else(|| anyhow::anyhow!("cannot hash produced file"))?,
    })
}

/// Capture a read-only file's content only while its observed first state still
/// matches. Callers restrict this opt-in contract to successful content opens in
/// the workspace; metadata-only observations remain strict FileState keys.
pub(crate) fn content_validated_key(
    path: &Path,
    initial: &DependencyKey,
    initial_id: Option<(u64, u64)>,
) -> Option<DependencyKey> {
    let DependencyKey::FileState {
        modified,
        changed_sec,
        changed_nsec,
        ..
    } = initial
    else {
        return None;
    };
    if !check_dependency(path, initial).ok()? {
        return None;
    }
    let file = capture_produced_file(path).ok()?;
    if initial_id != Some((file.device, file.inode)) || !check_dependency(path, initial).ok()? {
        return None;
    }
    Some(DependencyKey::FileContent {
        modified: *modified,
        changed_sec: *changed_sec,
        changed_nsec: *changed_nsec,
        file,
    })
}

fn check_dependency(path: &Path, key: &DependencyKey) -> Result<bool> {
    Ok(match key {
        DependencyKey::Overwrite { initial, output } => {
            if check_dependency(path, initial).unwrap_or(false) {
                true
            } else {
                let metadata = fs::symlink_metadata(path)?;
                metadata.is_file()
                    && metadata.dev() == output.device
                    && metadata.ino() == output.inode
                    && metadata.len() == output.size
                    && metadata.mode() == output.mode
                    && metadata.uid() == output.uid
                    && metadata.gid() == output.gid
                    && metadata.nlink() == output.links
                    && crate::ops::permissions::effective_access(path)? == output.access
                    && get_file_hash(path)? == Some(output.hash)
            }
        }
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
        DependencyKey::FileContent {
            modified,
            changed_sec,
            changed_nsec,
            file,
        } => {
            let before = fs::symlink_metadata(path)?;
            if !before.is_file() {
                return Ok(false);
            }
            let access = crate::ops::permissions::effective_access(path)?;
            let metadata_matches = before.len() == file.size
                && before.mode() == file.mode
                && before.uid() == file.uid
                && before.gid() == file.gid
                && before.nlink() == file.links
                && access == file.access
                && before.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() == *modified;
            if !metadata_matches {
                false
            } else if before.dev() == file.device
                && before.ino() == file.inode
                && before.ctime() == *changed_sec
                && before.ctime_nsec() == *changed_nsec
            {
                true
            } else if get_file_hash(path)? != Some(file.hash) {
                false
            } else {
                // Hashing must not bless a file that changed during validation.
                let after = fs::symlink_metadata(path)?;
                after.dev() == before.dev()
                    && after.ino() == before.ino()
                    && after.len() == before.len()
                    && after.mode() == before.mode()
                    && after.uid() == before.uid()
                    && after.gid() == before.gid()
                    && after.nlink() == before.nlink()
                    && after.ctime() == before.ctime()
                    && after.ctime_nsec() == before.ctime_nsec()
                    && after.modified()? == before.modified()?
            }
        }
        DependencyKey::NotDirectory => matches!(fs::symlink_metadata(path),
            Err(error) if error.kind() == ErrorKind::NotADirectory),
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

#[cfg(test)]
mod content_input_tests {
    use super::*;
    use std::fs::{File, FileTimes, Permissions};
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn content_validation_preserves_content_and_metadata_dependencies() -> Result<()> {
        let directory = std::env::temp_dir().join(format!("incr-content-{}", rand::random::<u128>()));
        fs::create_dir(&directory)?;
        let result = (|| -> Result<()> {
            let path = directory.join("input");
            fs::write(&path, b"original")?;
            let metadata = fs::metadata(&path)?;
            let initial = capture_dependency(&path, false)?;
            let key = content_validated_key(&path, &initial, Some((metadata.dev(), metadata.ino())))
                .expect("stable content input");
            assert!(content_validated_key(&path, &initial, None).is_none());
            let restore_time = || -> Result<()> {
                File::open(&path)?.set_times(FileTimes::new().set_modified(metadata.modified()?))?;
                Ok(())
            };
            std::thread::sleep(std::time::Duration::from_millis(20));
            fs::write(&path, b"original")?;
            restore_time()?;
            assert!(!check_dependency(&path, &initial)?);
            assert!(check_dependency(&path, &key)?);
            std::thread::sleep(std::time::Duration::from_millis(20));
            fs::write(&path, b"modified")?;
            restore_time()?;
            assert!(!check_dependency(&path, &key)?);
            assert!(content_validated_key(&path, &initial, Some((metadata.dev(), metadata.ino()))).is_none());
            let replacement = directory.join("replacement");
            fs::write(&replacement, b"original")?;
            fs::set_permissions(&replacement, Permissions::from_mode(metadata.mode()))?;
            fs::rename(&replacement, &path)?;
            restore_time()?;
            assert!(check_dependency(&path, &key)?);
            fs::set_permissions(&path, Permissions::from_mode(metadata.mode() ^ 0o100))?;
            assert!(!check_dependency(&path, &key)?);
            fs::remove_file(&path)?;
            std::os::unix::fs::symlink("missing", &path)?;
            assert!(!check_dependency(&path, &key)?);
            Ok(())
        })();
        fs::remove_dir_all(directory)?;
        result
    }
}
