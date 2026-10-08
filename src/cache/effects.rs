//! Filesystem effects captured after a completed Observe execution.
//! Replay is used only for a validated cache hit, never after a live cold run.
use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};

use crate::ops::permissions::{TemporaryPermissions, remove_tree};

const MANIFEST: &str = "effects.json";

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
        hash: u64,
        replace: bool,
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
                        hash: crate::ops::data::hash_stream(&mut fs::File::open(directory.join(&source))?)?,
                        source,
                        mode: metadata.mode(),
                        replace: replaced_paths.contains(path),
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
    let manifest = Manifest { version: 3, entries };
    let pending = directory.join("effects.pending");
    fs::write(&pending, serde_json::to_vec(&manifest)?)?;
    fs::rename(pending, directory.join(MANIFEST))?;
    Ok(())
}

fn load_validated(directory: &Path) -> Result<Manifest> {
    let manifest: Manifest = serde_json::from_slice(&fs::read(directory.join(MANIFEST))?)?;
    if manifest.version != 3 {
        bail!("unsupported filesystem effect version");
    }
    let mut seen = HashSet::new();
    let mut regular_files = HashSet::new();
    for entry in &manifest.entries {
        if !entry.path.is_absolute() || !seen.insert(entry.path.clone()) {
            bail!("invalid or duplicate cached output path");
        }
        if let Effect::File { source, hash, .. } = &entry.effect {
            if !matches!(
                Path::new(source).components().collect::<Vec<_>>().as_slice(),
                [std::path::Component::Normal(_)]
            ) {
                bail!("invalid cached file name");
            }
            let source = directory.join(source);
            if !fs::symlink_metadata(&source)?.is_file()
                || crate::ops::data::hash_stream(&mut fs::File::open(source)?)? != *hash
            {
                bail!("cached output content is incomplete or corrupt");
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
    // Validate every payload before applying even the first deletion.
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
