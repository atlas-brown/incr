use anyhow::Result;
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufReader, ErrorKind};
use std::os::unix::ffi::OsStringExt;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;
use xxhash_rust::xxh3::Xxh3;

use crate::cache::batch_cache::CacheCursor;
use crate::cache::{CacheData, DependencyKey};
use crate::command::Command;
use crate::config::{BUFFER_SIZE, Config, DYNAMIC_EXCLUDED_PATHS, INTROSPECT_DIRECTORY};
use crate::ops;
use crate::ops::debug_log;

pub(crate) fn check_cache_valid(cache: &CacheCursor<'_>, data: &CacheData) -> Result<bool> {
    if !data.replay_barriers.is_empty() {
        debug_log!(
            "[incr] command cache: replay barriers: {:?}",
            data.replay_barriers
        );
        return Ok(false);
    }
    if !cache.data_outputs_exist() {
        debug_log!("[incr] command cache: cached output stream is missing");
        return Ok(false);
    }
    if !check_read_dependencies(&data.read_dependencies)? {
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
                debug_log!(
                    "[incr] command cache: invalid dependency {} ({key:?})",
                    path.display()
                );
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
        DependencyKey::ContentState {
            modified,
            size,
            mode,
            uid,
            gid,
            access,
            hash,
        } => {
            let before = fs::symlink_metadata(path)?;
            if !before.is_file()
                || before.len() != *size
                || before.mode() != *mode
                || before.uid() != *uid
                || before.gid() != *gid
                || crate::ops::permissions::effective_access(path)? != *access
                || before.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() != *modified
            {
                return Ok(false);
            }
            if get_file_hash(path)? != Some(*hash) {
                return Ok(false);
            }
            let after = fs::symlink_metadata(path)?;
            before.dev() == after.dev()
                && before.ino() == after.ino()
                && before.len() == after.len()
                && before.mode() == after.mode()
                && before.uid() == after.uid()
                && before.gid() == after.gid()
                && before.mtime() == after.mtime()
                && before.mtime_nsec() == after.mtime_nsec()
                && before.ctime() == after.ctime()
                && before.ctime_nsec() == after.ctime_nsec()
        }
        DependencyKey::ContentHashState {
            size,
            mode,
            uid,
            gid,
            access,
            hash,
        } => {
            let before = fs::symlink_metadata(path)?;
            if !before.is_file()
                || before.len() != *size
                || before.mode() != *mode
                || before.uid() != *uid
                || before.gid() != *gid
                || crate::ops::permissions::effective_access(path)? != *access
            {
                return Ok(false);
            }
            if get_file_hash(path)? != Some(*hash) {
                return Ok(false);
            }
            let after = fs::symlink_metadata(path)?;
            before.dev() == after.dev()
                && before.ino() == after.ino()
                && before.len() == after.len()
                && before.mode() == after.mode()
                && before.uid() == after.uid()
                && before.gid() == after.gid()
                && before.mtime() == after.mtime()
                && before.mtime_nsec() == after.mtime_nsec()
                && before.ctime() == after.ctime()
                && before.ctime_nsec() == after.ctime_nsec()
        }
        DependencyKey::ExtendedAttributes(hash) => extended_attributes_hash(path)? == *hash,
        DependencyKey::DockerDirectoryState {
            entry_hash,
            mode,
            uid,
            gid,
            access,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            let current_hash = get_directory_hash(path)?;
            let valid = metadata.is_dir()
                && metadata.mode() == *mode
                && metadata.uid() == *uid
                && metadata.gid() == *gid
                && crate::ops::permissions::effective_access(path)? == *access
                && current_hash == Some(*entry_hash);
            if !valid {
                debug_log!(
                    "[incr] command cache: directory state {} expected (hash {entry_hash}, mode {mode}, uid {uid}, gid {gid}, access {access}); current (hash {current_hash:?}, mode {}, uid {}, gid {})",
                    path.display(),
                    metadata.mode(),
                    metadata.uid(),
                    metadata.gid()
                );
            }
            valid
        }

        DependencyKey::DockerSymlinkState {
            target,
            modified,
            mode,
            uid,
            gid,
        } => {
            let metadata = fs::symlink_metadata(path)?;
            metadata.file_type().is_symlink()
                && metadata.mode() == *mode
                && metadata.uid() == *uid
                && metadata.gid() == *gid
                && metadata.modified()?.duration_since(UNIX_EPOCH)?.as_nanos() == *modified
                && fs::read_link(path)? == *target
        }
        DependencyKey::DoesNotExist => matches!(
            fs::symlink_metadata(path),
            Err(error) if matches!(error.kind(), ErrorKind::NotFound | ErrorKind::NotADirectory)
        ),
        DependencyKey::Hash(hash) => path.is_file() && get_file_hash(path)? == Some(*hash),
    })
}

fn extended_attributes_hash(path: &Path) -> Result<u64> {
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;

    let path = CString::new(path.as_os_str().as_bytes())?;
    let length = unsafe { libc::llistxattr(path.as_ptr(), std::ptr::null_mut(), 0) };
    if length < 0 {
        let error = std::io::Error::last_os_error();
        if error.raw_os_error() == Some(libc::ENOTSUP) {
            return Ok(xxhash_rust::xxh3::Xxh3::new().digest());
        }
        return Err(error.into());
    }
    let mut names = vec![0u8; length as usize];
    let length = unsafe { libc::llistxattr(path.as_ptr(), names.as_mut_ptr().cast(), names.len()) };
    if length < 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    names.truncate(length as usize);
    let mut names = names
        .split(|byte| *byte == 0)
        .filter(|name| !name.is_empty())
        .map(<[u8]>::to_vec)
        .collect::<Vec<_>>();
    names.sort_unstable();
    let mut hasher = xxhash_rust::xxh3::Xxh3::new();
    for name in names {
        hasher.update(&(name.len() as u64).to_le_bytes());
        hasher.update(&name);
        let name = CString::new(name)?;
        let length = unsafe { libc::lgetxattr(path.as_ptr(), name.as_ptr(), std::ptr::null_mut(), 0) };
        if length < 0 {
            return Err(std::io::Error::last_os_error().into());
        }
        let mut value = vec![0u8; length as usize];
        let length = unsafe {
            libc::lgetxattr(
                path.as_ptr(),
                name.as_ptr(),
                value.as_mut_ptr().cast(),
                value.len(),
            )
        };
        if length < 0 {
            return Err(std::io::Error::last_os_error().into());
        }
        value.truncate(length as usize);
        hasher.update(&(value.len() as u64).to_le_bytes());
        hasher.update(&value);
    }
    Ok(hasher.digest())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;

    struct TestDirectory(PathBuf);

    impl TestDirectory {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "incr-dependency-test-{}-{}",
                std::process::id(),
                rand::random::<u64>()
            ));
            fs::create_dir(&path).unwrap();
            Self(path)
        }

        fn path(&self) -> &Path {
            &self.0
        }
    }

    impl Drop for TestDirectory {
        fn drop(&mut self) {
            fs::remove_dir_all(&self.0).unwrap();
        }
    }

    fn content_state(path: &Path) -> DependencyKey {
        let metadata = fs::symlink_metadata(path).unwrap();
        DependencyKey::ContentState {
            modified: metadata
                .modified()
                .unwrap()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            size: metadata.len(),
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            access: crate::ops::permissions::effective_access(path).unwrap(),
            hash: get_file_hash(path).unwrap().unwrap(),
        }
    }

    fn content_hash_state(path: &Path) -> DependencyKey {
        let metadata = fs::symlink_metadata(path).unwrap();
        DependencyKey::ContentHashState {
            size: metadata.len(),
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            access: crate::ops::permissions::effective_access(path).unwrap(),
            hash: get_file_hash(path).unwrap().unwrap(),
        }
    }

    fn restore_mtime(path: &Path, metadata: &fs::Metadata) {
        let path = CString::new(path.as_os_str().as_bytes()).unwrap();
        let times = [
            libc::timespec {
                tv_sec: 0,
                tv_nsec: libc::UTIME_OMIT,
            },
            libc::timespec {
                tv_sec: metadata.mtime(),
                tv_nsec: metadata.mtime_nsec() as _,
            },
        ];
        assert_eq!(
            unsafe { libc::utimensat(libc::AT_FDCWD, path.as_ptr(), times.as_ptr(), 0) },
            0
        );
    }

    #[test]
    fn content_dependency_accepts_same_content_after_inode_and_ctime_change() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        let replacement = directory.path().join("replacement");
        fs::write(&path, b"stable input").unwrap();
        let dependency = content_state(&path);
        let original = fs::symlink_metadata(&path).unwrap();
        fs::rename(&path, &replacement).unwrap();
        fs::write(&path, b"stable input").unwrap();
        restore_mtime(&path, &original);

        let replaced = fs::symlink_metadata(&path).unwrap();
        assert_ne!(original.ino(), replaced.ino());
        assert_ne!(
            (original.ctime(), original.ctime_nsec()),
            (replaced.ctime(), replaced.ctime_nsec())
        );
        assert!(check_dependency(&path, &dependency).unwrap());
    }

    #[test]
    fn content_dependency_rejects_changed_content_with_restored_mtime() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        fs::write(&path, b"original").unwrap();
        let dependency = content_state(&path);
        let original = fs::symlink_metadata(&path).unwrap();
        fs::write(&path, b"modified").unwrap();
        restore_mtime(&path, &original);

        assert!(!check_dependency(&path, &dependency).unwrap());
    }

    #[test]
    fn content_hash_dependency_accepts_timestamp_only_changes() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        fs::write(&path, b"unchanged content").unwrap();
        let dependency = content_hash_state(&path);
        let path_c = CString::new(path.as_os_str().as_bytes()).unwrap();
        let times = [
            libc::timespec {
                tv_sec: 0,
                tv_nsec: libc::UTIME_OMIT,
            },
            libc::timespec {
                tv_sec: 1_700_000_000,
                tv_nsec: 0,
            },
        ];
        assert_eq!(
            unsafe { libc::utimensat(libc::AT_FDCWD, path_c.as_ptr(), times.as_ptr(), 0) },
            0
        );

        assert!(check_dependency(&path, &dependency).unwrap());
    }

    #[test]
    fn content_hash_dependency_rejects_changed_bytes() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        fs::write(&path, b"original").unwrap();
        let dependency = content_hash_state(&path);
        fs::write(&path, b"modified").unwrap();

        assert!(!check_dependency(&path, &dependency).unwrap());
    }

    #[test]
    fn missing_path_beneath_a_file_is_valid_while_parent_dependency_guards_it() {
        let directory = TestDirectory::new();
        let parent = directory.path().join("README.md");
        let nested = parent.join("install.sh");
        fs::write(&parent, b"not a directory").unwrap();
        let parent_dependency = capture_dependency(&parent, false).unwrap();
        let nested_dependency = DependencyKey::DoesNotExist;

        assert!(check_dependency(&parent, &parent_dependency).unwrap());
        assert!(check_dependency(&nested, &nested_dependency).unwrap());

        fs::remove_file(&parent).unwrap();
        fs::create_dir(&parent).unwrap();

        assert!(!check_dependency(&parent, &parent_dependency).unwrap());
        assert!(check_dependency(&nested, &nested_dependency).unwrap());
    }

    #[test]
    fn extended_attribute_dependency_rejects_changed_values() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        fs::write(&path, b"unchanged content").unwrap();
        set_xattr(&path, b"user.incr-cache", b"original");
        let dependency = DependencyKey::ExtendedAttributes(extended_attributes_hash(&path).unwrap());

        set_xattr(&path, b"user.incr-cache", b"changed");

        assert!(!check_dependency(&path, &dependency).unwrap());
    }

    fn set_xattr(path: &Path, name: &[u8], value: &[u8]) {
        let path = CString::new(path.as_os_str().as_bytes()).unwrap();
        let name = CString::new(name).unwrap();
        assert_eq!(
            unsafe {
                libc::setxattr(
                    path.as_ptr(),
                    name.as_ptr(),
                    value.as_ptr().cast(),
                    value.len(),
                    0,
                )
            },
            0
        );
    }

    #[test]
    fn docker_directory_dependency_detects_entry_changes() {
        let directory = TestDirectory::new();
        let path = directory.path().join("input");
        fs::create_dir(&path).unwrap();
        let metadata = fs::symlink_metadata(&path).unwrap();
        let dependency = DependencyKey::DockerDirectoryState {
            entry_hash: get_directory_hash(&path).unwrap().unwrap(),
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            access: crate::ops::permissions::effective_access(&path).unwrap(),
        };
        std::thread::sleep(std::time::Duration::from_millis(2));
        fs::write(path.join("new-entry"), b"data").unwrap();

        assert!(!check_dependency(&path, &dependency).unwrap());
    }

    #[test]
    fn parent_directory_dependency_ignores_unrelated_entry_changes() {
        let directory = TestDirectory::new();
        let metadata = fs::symlink_metadata(directory.path()).unwrap();
        let dependency = DependencyKey::ParentDirectory {
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            access: crate::ops::permissions::effective_access(directory.path()).unwrap(),
        };

        fs::write(directory.path().join("unrelated-entry"), b"data").unwrap();

        assert!(check_dependency(directory.path(), &dependency).unwrap());
    }
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

fn get_directory_hash(directory: &Path) -> Result<Option<u64>> {
    let before = fs::symlink_metadata(directory)?;
    if !before.is_dir() {
        return Ok(None);
    }
    let mut entries = fs::read_dir(directory)?
        .map(|entry| {
            let entry = entry?;
            let file_type = entry.file_type()?;
            let kind = if file_type.is_dir() {
                1
            } else if file_type.is_file() {
                2
            } else if file_type.is_symlink() {
                3
            } else {
                4
            };
            Ok((entry.file_name().into_vec(), kind))
        })
        .collect::<Result<Vec<_>>>()?;
    entries.sort_unstable_by(|left, right| left.0.cmp(&right.0));

    let mut hasher = Xxh3::new();
    for (name, kind) in entries {
        hasher.update(&(name.len() as u64).to_le_bytes());
        hasher.update(&name);
        hasher.update(&[kind]);
    }
    let after = fs::symlink_metadata(directory)?;
    let stable = before.dev() == after.dev()
        && before.ino() == after.ino()
        && before.mtime() == after.mtime()
        && before.mtime_nsec() == after.mtime_nsec()
        && before.ctime() == after.ctime()
        && before.ctime_nsec() == after.ctime_nsec()
        && before.len() == after.len()
        && before.mode() == after.mode()
        && before.uid() == after.uid()
        && before.gid() == after.gid();
    Ok(stable.then_some(hasher.digest()))
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
