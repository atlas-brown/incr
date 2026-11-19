//! `--hash-dependencies` and a content-hash cache keyed by stat.
//! Files changed within `RACY_WINDOW` are not cached (racy git).
use anyhow::Result;
use std::fs::{self, File, Metadata};
use std::io::{BufReader, Write};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const RACY_WINDOW: Duration = Duration::from_secs(2);
const BUFFER_SIZE: usize = 1 << 16;

struct State {
    enabled: bool,
    directory: Option<PathBuf>,
}

static STATE: OnceLock<State> = OnceLock::new();

/// Called once at startup.
pub(crate) fn init(enabled: bool, cache_directory: &Path) {
    let _ = STATE.set(State {
        enabled,
        directory: enabled.then(|| cache_directory.join("file-hashes")),
    });
}

/// Whether `--hash-dependencies` is on.
pub(crate) fn enabled() -> bool {
    STATE.get().is_some_and(|state| state.enabled)
}

fn stat_key(path: &Path, metadata: &Metadata) -> u64 {
    let mut bytes = path.as_os_str().as_bytes().to_vec();
    for value in [
        metadata.ino(),
        metadata.ctime() as u64,
        metadata.ctime_nsec() as u64,
        metadata.mtime() as u64,
        metadata.mtime_nsec() as u64,
        metadata.len(),
    ] {
        bytes.extend_from_slice(&value.to_le_bytes());
    }
    super::data::hash_bytes(&bytes)
}

fn same_stat(before: &Metadata, after: &Metadata) -> bool {
    before.ino() == after.ino()
        && before.len() == after.len()
        && before.mtime() == after.mtime()
        && before.mtime_nsec() == after.mtime_nsec()
        && before.ctime() == after.ctime()
        && before.ctime_nsec() == after.ctime_nsec()
}

fn settled(metadata: &Metadata) -> bool {
    let ctime = UNIX_EPOCH + Duration::new(metadata.ctime() as u64, metadata.ctime_nsec() as u32);
    SystemTime::now()
        .duration_since(ctime)
        .is_ok_and(|age| age >= RACY_WINDOW)
}

/// Content hash of `file`, cached when enabled.
pub(crate) fn hash_open_file(path: &Path, file: File, metadata: &Metadata) -> Result<u64> {
    let directory = STATE.get().and_then(|state| state.directory.as_deref());
    hash_open_file_in(directory, path, file, metadata)
}

fn hash_open_file_in(
    directory: Option<&Path>,
    path: &Path,
    file: File,
    metadata: &Metadata,
) -> Result<u64> {
    let entry = directory.map(|directory| directory.join(format!("{:016x}", stat_key(path, metadata))));
    if let Some(entry) = &entry
        && let Ok(bytes) = fs::read(entry)
        && let Ok(bytes) = <[u8; 8]>::try_from(bytes.as_slice())
    {
        return Ok(u64::from_le_bytes(bytes));
    }
    let mut reader = BufReader::with_capacity(BUFFER_SIZE, file);
    let hash = super::data::hash_stream(&mut reader)?;
    if let Some(entry) = entry
        && settled(metadata)
        && fs::symlink_metadata(path).is_ok_and(|after| same_stat(metadata, &after))
    {
        store(&entry, hash);
    }
    Ok(hash)
}

fn store(entry: &Path, hash: u64) {
    let Some(directory) = entry.parent() else {
        return;
    };
    // Atomic write.
    let temporary = directory.join(format!(".tmp-{}-{}", std::process::id(), rand::random::<u64>()));
    let written = fs::create_dir_all(directory).is_ok()
        && File::create(&temporary)
            .and_then(|mut file| file.write_all(&hash.to_le_bytes()))
            .is_ok();
    if !written || fs::rename(&temporary, entry).is_err() {
        let _ = fs::remove_file(&temporary);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn scratch() -> PathBuf {
        let directory = std::env::temp_dir().join(format!("incr-hash-cache-{}", rand::random::<u128>()));
        fs::create_dir(&directory).unwrap();
        directory
    }

    fn hash(cache: &Path, path: &Path) -> u64 {
        let file = File::open(path).unwrap();
        let metadata = file.metadata().unwrap();
        hash_open_file_in(Some(cache), path, file, &metadata).unwrap()
    }

    #[test]
    fn fresh_file_is_hashed_but_not_cached() {
        let directory = scratch();
        let cache = directory.join("cache");
        let path = directory.join("f");
        fs::write(&path, b"one").unwrap();
        assert_eq!(hash(&cache, &path), super::super::data::hash_bytes(b"one"));
        // Its ctime is within the racy window: nothing stored.
        assert!(fs::read_dir(&cache).map_or(true, |mut entries| entries.next().is_none()));
        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn matching_stat_reads_the_cached_hash() {
        let directory = scratch();
        let cache = directory.join("cache");
        let path = directory.join("f");
        fs::write(&path, b"one").unwrap();
        let entry = cache.join(format!("{:016x}", stat_key(&path, &fs::metadata(&path).unwrap())));
        store(&entry, 0xfeed);
        assert_eq!(hash(&cache, &path), 0xfeed); // served from the cache, not read
        fs::remove_dir_all(directory).unwrap();
    }

    #[test]
    fn rewrite_with_same_bytes_misses_the_cache_and_rehashes() {
        let directory = scratch();
        let cache = directory.join("cache");
        let path = directory.join("f");
        fs::write(&path, b"same").unwrap();
        let entry = cache.join(format!("{:016x}", stat_key(&path, &fs::metadata(&path).unwrap())));
        store(&entry, 0xbad);
        std::thread::sleep(Duration::from_millis(20));
        let temporary = directory.join("g");
        fs::write(&temporary, b"same").unwrap();
        fs::rename(&temporary, &path).unwrap(); // new inode and ctime, same bytes
        assert_eq!(hash(&cache, &path), super::super::data::hash_bytes(b"same"));
        fs::remove_dir_all(directory).unwrap();
    }
}
