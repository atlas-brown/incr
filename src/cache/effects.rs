//! Filesystem effects captured after a completed Observe execution.
//! Replay is used only for a validated cache hit, never after a live cold run.
use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::os::fd::AsRawFd;
use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};

use crate::ops::permissions::{TemporaryPermissions, remove_tree};

const MANIFEST: &str = "effects.json";
const MANIFEST_VERSION: u32 = 5;

#[derive(Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum Effect {
    Missing,
    Directory {
        mode: u32,
    },
    Symlink {
        target: PathBuf,
    },
    File {
        source: String,
        mode: u32,
        replace: bool,
        modified_sec: i64,
        modified_nsec: i64,
    },
    HardLink {
        target: PathBuf,
    },
}

#[derive(Serialize, Deserialize)]
struct Entry {
    path: PathBuf,
    effect: Effect,
}

#[derive(Serialize, Deserialize)]
struct Manifest {
    version: u32,
    entries: Vec<Entry>,
}

pub(crate) fn capture(
    directory: &Path,
    writes: &HashSet<PathBuf>,
    replaced_paths: &HashSet<PathBuf>,
) -> Result<()> {
    fs::create_dir_all(directory)?;
    let mut paths: Vec<_> = writes.iter().collect();
    paths.sort();
    let mut inodes = HashMap::new();
    let mut entries = Vec::new();
    for path in paths {
        let effect = match fs::symlink_metadata(path) {
            Err(error)
                if matches!(
                    error.kind(),
                    std::io::ErrorKind::NotFound | std::io::ErrorKind::NotADirectory
                ) =>
            {
                Effect::Missing
            }
            Err(error) => return Err(error).with_context(|| format!("capture {}", path.display())),
            Ok(metadata) if metadata.file_type().is_symlink() => Effect::Symlink {
                target: fs::read_link(path)?,
            },
            Ok(metadata) if metadata.is_dir() => Effect::Directory {
                mode: metadata.mode(),
            },
            Ok(metadata) if metadata.is_file() => {
                let inode = (metadata.dev(), metadata.ino());
                if let Some(target) = inodes.get(&inode) {
                    Effect::HardLink {
                        target: PathBuf::clone(target),
                    }
                } else {
                    let source = format!("file-{}", entries.len());
                    fs::copy(path, directory.join(&source))?;
                    inodes.insert(inode, path.clone());
                    Effect::File {
                        source,
                        mode: metadata.mode(),
                        replace: replaced_paths.contains(path),
                        modified_sec: metadata.mtime(),
                        modified_nsec: metadata.mtime_nsec(),
                    }
                }
            }
            Ok(_) => continue, // Device/FIFO content is not a replayable regular file.
        };
        entries.push(Entry {
            path: path.clone(),
            effect,
        });
    }
    let manifest = Manifest {
        version: MANIFEST_VERSION,
        entries,
    };
    let pending = directory.join("effects.pending");
    fs::write(&pending, serde_json::to_vec(&manifest)?)?;
    fs::rename(pending, directory.join(MANIFEST))?;
    Ok(())
}

fn load_validated(directory: &Path) -> Result<Manifest> {
    let manifest: Manifest = serde_json::from_slice(&fs::read(directory.join(MANIFEST))?)?;
    if manifest.version != MANIFEST_VERSION {
        bail!("unsupported filesystem effect version");
    }
    let mut seen = HashSet::new();
    let mut regular_files = HashSet::new();
    for entry in &manifest.entries {
        if !entry.path.is_absolute() || !seen.insert(entry.path.clone()) {
            bail!("invalid or duplicate cached output path");
        }
        if let Effect::File {
            source,
            modified_nsec,
            ..
        } = &entry.effect
        {
            if !(0..1_000_000_000).contains(modified_nsec) {
                bail!("invalid cached file timestamp");
            }
            if !matches!(
                Path::new(source).components().collect::<Vec<_>>().as_slice(),
                [std::path::Component::Normal(_)]
            ) {
                bail!("invalid cached file name");
            }
            let source = directory.join(source);
            if !fs::symlink_metadata(&source)?.is_file() {
                bail!("cached output payload is not a regular file");
            }
        }
        match &entry.effect {
            Effect::File { .. } => {
                regular_files.insert(entry.path.clone());
            }
            Effect::HardLink { target } => {
                if !regular_files.contains(target) || target == &entry.path {
                    bail!("invalid cached hard link target");
                }
                regular_files.insert(entry.path.clone());
            }
            _ => (),
        }
    }
    Ok(manifest)
}

pub(crate) fn valid(directory: &Path) -> bool {
    load_validated(directory).is_ok()
}

pub(crate) fn replay(directory: &Path) -> Result<()> {
    // Validate manifest structure and payload presence before applying deletions.
    // Payload bytes belong to the trusted private cache, as do cached streams.
    let manifest = load_validated(directory)?;
    let managed_paths: HashSet<_> = manifest
        .entries
        .iter()
        .map(|entry| entry.path.as_path())
        .collect();
    for entry in manifest.entries.iter().rev() {
        if matches!(entry.effect, Effect::Missing) {
            TemporaryPermissions::with_parents(&entry.path, &managed_paths, || remove_tree(&entry.path))?;
        }
    }
    for entry in &manifest.entries {
        if !matches!(entry.effect, Effect::Missing) {
            TemporaryPermissions::with_parents(&entry.path, &managed_paths, || {
                replay_entry(directory, entry)
            })?;
        }
    }
    // Children are installed before read-only parent modes become final.
    for entry in manifest.entries.iter().rev() {
        if let Effect::Directory { mode } = entry.effect {
            TemporaryPermissions::with_parents(&entry.path, &managed_paths, || {
                fs::set_permissions(&entry.path, fs::Permissions::from_mode(mode))?;
                Ok(())
            })?;
        }
    }
    Ok(())
}

fn replay_entry(directory: &Path, entry: &Entry) -> Result<()> {
    let path = &entry.path;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    match &entry.effect {
        Effect::Missing => (),
        Effect::Directory { .. } => {
            if fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.is_dir()) {
                remove_tree(path)?;
            }
            fs::create_dir_all(path)?;
        }
        Effect::Symlink { target } => {
            remove_tree(path)?;
            symlink(target, path)?;
        }
        Effect::File {
            source,
            mode,
            replace,
            modified_sec,
            modified_nsec,
            ..
        } => {
            if *replace || fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.is_file()) {
                remove_tree(path)?;
            }
            TemporaryPermissions::with_file(path, || {
                // Copy bytes without chmod/chown: group access need not imply ownership.
                let mut source = fs::File::open(directory.join(source))?;
                let mut destination = fs::File::create(path)?;
                std::io::copy(&mut source, &mut destination)?;
                if destination.metadata()?.mode() & 0o7777 != mode & 0o7777 {
                    destination.set_permissions(fs::Permissions::from_mode(*mode))?;
                }
                // Like original Incr's cp -p, preserve a cached output's mtime.
                // Otherwise replay alone invalidates downstream content inputs.
                let times = [
                    libc::timespec {
                        tv_sec: 0,
                        tv_nsec: libc::UTIME_OMIT,
                    },
                    libc::timespec {
                        tv_sec: *modified_sec,
                        tv_nsec: *modified_nsec,
                    },
                ];
                if unsafe { libc::futimens(destination.as_raw_fd(), times.as_ptr()) } != 0 {
                    let error = std::io::Error::last_os_error();
                    // Group write access need not include permission to set a
                    // historical timestamp. Keep such replay available; the
                    // changed timestamp conservatively invalidates consumers.
                    if !matches!(error.raw_os_error(), Some(libc::EPERM | libc::EACCES)) {
                        return Err(error.into());
                    }
                }
                Ok(())
            })?;
        }
        Effect::HardLink { target } => {
            let target_metadata = fs::metadata(target)?;
            let already_linked = fs::symlink_metadata(path).is_ok_and(|metadata| {
                metadata.is_file()
                    && metadata.dev() == target_metadata.dev()
                    && metadata.ino() == target_metadata.ino()
            });
            // Parent symlinks can make both paths name the same directory entry.
            if !already_linked {
                remove_tree(path)?;
                fs::hard_link(target, path)?;
            }
        }
    }
    Ok(())
}

pub(crate) fn exists(directory: &Path) -> bool {
    directory.join(MANIFEST).is_file()
}

#[cfg(test)]
mod tests;
