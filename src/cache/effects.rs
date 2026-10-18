//! Filesystem effects captured after a completed Observe execution.
//! Replay is used only for a validated cache hit, never after a live cold run.
use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::ffi::CString;
use std::fs;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};

use crate::ops::permissions::{TemporaryPermissions, remove_tree};

const MANIFEST: &str = "effects.json";

#[derive(Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum Effect {
    Missing,
    Directory {
        metadata: MetadataState,
    },
    Symlink {
        target: PathBuf,
        metadata: MetadataState,
    },
    File {
        source: String,
        metadata: MetadataState,
        hash: u64,
        replace: bool,
    },
    HardLink {
        target: PathBuf,
    },
}

#[derive(Serialize, Deserialize)]
struct MetadataState {
    mode: u32,
    uid: u32,
    gid: u32,
    mtime_sec: i64,
    mtime_nsec: i64,
    extended_attributes: Vec<ExtendedAttribute>,
}

#[derive(Serialize, Deserialize)]
struct ExtendedAttribute {
    name: Vec<u8>,
    value: Vec<u8>,
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
    dependencies: &HashMap<PathBuf, crate::cache::DependencyKey>,
) -> Result<()> {
    fs::create_dir_all(directory)?;
    let mut paths: Vec<_> = writes.iter().collect();
    paths.sort();
    let write_paths = writes;
    let mut output_inodes = HashMap::new();
    for path in &paths {
        if let Ok(metadata) = fs::symlink_metadata(path)
            && metadata.is_file()
        {
            output_inodes
                .entry((metadata.dev(), metadata.ino()))
                .or_insert_with(|| (*path).clone());
        }
    }
    let mut input_inodes = HashMap::new();
    for (path, dependency) in dependencies {
        if write_paths.contains(path) || !dependency.is_reusable() {
            continue;
        }
        if let Ok(metadata) = fs::symlink_metadata(path)
            && metadata.is_file()
        {
            input_inodes
                .entry((metadata.dev(), metadata.ino()))
                .or_insert_with(|| path.clone());
        }
    }
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
                metadata: MetadataState::capture(path, &metadata)?,
            },
            Ok(metadata) if metadata.is_dir() => Effect::Directory {
                metadata: MetadataState::capture(path, &metadata)?,
            },
            Ok(metadata) if metadata.is_file() => {
                let inode = (metadata.dev(), metadata.ino());
                if let Some(target) = output_inodes
                    .get(&inode)
                    .filter(|target| *target != path)
                    .or_else(|| input_inodes.get(&inode))
                {
                    Effect::HardLink {
                        target: PathBuf::clone(target),
                    }
                } else {
                    let source = format!("file-{}", entries.len());
                    fs::copy(path, directory.join(&source))?;
                    Effect::File {
                        hash: crate::ops::data::hash_stream(&mut fs::File::open(directory.join(&source))?)?,
                        source,
                        metadata: MetadataState::capture(path, &metadata)?,
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
    let manifest = Manifest { version: 5, entries };
    let pending = directory.join("effects.pending");
    fs::write(&pending, serde_json::to_vec(&manifest)?)?;
    fs::rename(pending, directory.join(MANIFEST))?;
    Ok(())
}

fn load_validated(directory: &Path) -> Result<Manifest> {
    let manifest: Manifest = serde_json::from_slice(&fs::read(directory.join(MANIFEST))?)?;
    if manifest.version != 5 {
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
                let target_is_cached_output = regular_files.contains(target);
                let target_is_external_file = !target_is_cached_output
                    && target != &entry.path
                    && fs::symlink_metadata(target).is_ok_and(|metadata| metadata.is_file());
                if (!target_is_cached_output && !target_is_external_file) || target == &entry.path {
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
        if let Effect::Directory { .. } = entry.effect {
            TemporaryPermissions::with_parents(&entry.path, &managed_paths, || {
                if let Some(metadata) = metadata_for(&entry.effect) {
                    apply_metadata(&entry.path, metadata, false)?;
                }
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
        Effect::Symlink { target, .. } => {
            remove_tree(path)?;
            symlink(target, path)?;
        }
        Effect::File { source, replace, .. } => {
            if *replace || fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.is_file()) {
                remove_tree(path)?;
            }
            TemporaryPermissions::with_file(path, || {
                // Copy bytes without chmod/chown: group access need not imply ownership.
                let mut source = fs::File::open(directory.join(source))?;
                let mut destination = fs::File::create(path)?;
                std::io::copy(&mut source, &mut destination)?;
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
    if let Some(metadata) = metadata_for(&entry.effect) {
        apply_metadata(path, metadata, matches!(entry.effect, Effect::Symlink { .. }))?;
    }
    Ok(())
}

impl MetadataState {
    fn capture(path: &Path, metadata: &fs::Metadata) -> Result<Self> {
        Ok(Self {
            mode: metadata.mode(),
            uid: metadata.uid(),
            gid: metadata.gid(),
            mtime_sec: metadata.mtime(),
            mtime_nsec: metadata.mtime_nsec(),
            extended_attributes: capture_extended_attributes(path)?,
        })
    }
}

fn metadata_for(effect: &Effect) -> Option<&MetadataState> {
    match effect {
        Effect::Directory { metadata } | Effect::Symlink { metadata, .. } | Effect::File { metadata, .. } => {
            Some(metadata)
        }
        Effect::Missing | Effect::HardLink { .. } => None,
    }
}

fn apply_metadata(path: &Path, metadata: &MetadataState, symlink: bool) -> Result<()> {
    let path_c = CString::new(path.as_os_str().as_bytes())?;
    unsafe {
        let current = fs::symlink_metadata(path)?;
        if current.uid() != metadata.uid || current.gid() != metadata.gid {
            let result = if symlink {
                libc::lchown(path_c.as_ptr(), metadata.uid, metadata.gid)
            } else {
                libc::chown(path_c.as_ptr(), metadata.uid, metadata.gid)
            };
            if result != 0 {
                return Err(std::io::Error::last_os_error().into());
            }
        }
        if !symlink
            && fs::symlink_metadata(path)?.mode() & 0o7777 != metadata.mode & 0o7777
            && libc::chmod(path_c.as_ptr(), metadata.mode as libc::mode_t) != 0
        {
            return Err(std::io::Error::last_os_error().into());
        }
        let times = [
            libc::timespec {
                tv_sec: 0,
                tv_nsec: libc::UTIME_OMIT,
            },
            libc::timespec {
                tv_sec: metadata.mtime_sec,
                tv_nsec: metadata.mtime_nsec as _,
            },
        ];
        let flags = if symlink { libc::AT_SYMLINK_NOFOLLOW } else { 0 };
        if libc::utimensat(libc::AT_FDCWD, path_c.as_ptr(), times.as_ptr(), flags) != 0 {
            return Err(std::io::Error::last_os_error().into());
        }
    }
    apply_extended_attributes(path, &metadata.extended_attributes)
}

fn capture_extended_attributes(path: &Path) -> Result<Vec<ExtendedAttribute>> {
    let path = CString::new(path.as_os_str().as_bytes())?;
    let length = unsafe { libc::llistxattr(path.as_ptr(), std::ptr::null_mut(), 0) };
    if length < 0 {
        let error = std::io::Error::last_os_error();
        if error.raw_os_error() == Some(libc::ENOTSUP) {
            return Ok(Vec::new());
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
    names
        .into_iter()
        .map(|name| {
            let name_c = CString::new(name.as_slice())?;
            let length = unsafe { libc::lgetxattr(path.as_ptr(), name_c.as_ptr(), std::ptr::null_mut(), 0) };
            if length < 0 {
                return Err(std::io::Error::last_os_error().into());
            }
            let mut value = vec![0u8; length as usize];
            let length = unsafe {
                libc::lgetxattr(
                    path.as_ptr(),
                    name_c.as_ptr(),
                    value.as_mut_ptr().cast(),
                    value.len(),
                )
            };
            if length < 0 {
                return Err(std::io::Error::last_os_error().into());
            }
            value.truncate(length as usize);
            Ok(ExtendedAttribute { name, value })
        })
        .collect()
}

fn apply_extended_attributes(path: &Path, attributes: &[ExtendedAttribute]) -> Result<()> {
    let path_c = CString::new(path.as_os_str().as_bytes())?;
    let length = unsafe { libc::llistxattr(path_c.as_ptr(), std::ptr::null_mut(), 0) };
    let current_names = if length < 0 {
        let error = std::io::Error::last_os_error();
        if error.raw_os_error() == Some(libc::ENOTSUP) {
            Vec::new()
        } else {
            return Err(error.into());
        }
    } else {
        let mut names = vec![0u8; length as usize];
        let length = unsafe { libc::llistxattr(path_c.as_ptr(), names.as_mut_ptr().cast(), names.len()) };
        if length < 0 {
            return Err(std::io::Error::last_os_error().into());
        }
        names.truncate(length as usize);
        names
            .split(|byte| *byte == 0)
            .filter(|name| !name.is_empty())
            .map(<[u8]>::to_vec)
            .collect::<Vec<_>>()
    };
    for name in current_names {
        if attributes.iter().any(|attribute| attribute.name == name) {
            continue;
        }
        let name_c = CString::new(name)?;
        if unsafe { libc::lremovexattr(path_c.as_ptr(), name_c.as_ptr()) } != 0 {
            let error = std::io::Error::last_os_error();
            if error.raw_os_error() != Some(libc::ENODATA) {
                return Err(error.into());
            }
        }
    }
    for attribute in attributes {
        let name = CString::new(attribute.name.as_slice())?;
        if unsafe {
            libc::lsetxattr(
                path_c.as_ptr(),
                name.as_ptr(),
                attribute.value.as_ptr().cast(),
                attribute.value.len(),
                0,
            )
        } != 0
        {
            return Err(std::io::Error::last_os_error().into());
        }
    }
    Ok(())
}

pub(crate) fn exists(directory: &Path) -> bool {
    directory.join(MANIFEST).is_file()
}

#[cfg(test)]
mod tests;
