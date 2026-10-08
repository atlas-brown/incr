//! Filesystem effects captured after a completed Observe execution.
//! Replay is used only for a validated cache hit, never after a live cold run.
use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt, symlink};
use std::path::{Path, PathBuf};

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
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Effect::Missing,
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

fn remove(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() => fs::remove_dir_all(path)?,
        Ok(_) => fs::remove_file(path)?,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => (),
        Err(error) => return Err(error.into()),
    }
    Ok(())
}

fn load_validated(directory: &Path) -> Result<Manifest> {
    let manifest: Manifest = serde_json::from_slice(&fs::read(directory.join(MANIFEST))?)?;
    if manifest.version != 3 {
        bail!("unsupported filesystem effect version");
    }
    let mut seen = HashSet::new();
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
        if let Effect::HardLink { target } = &entry.effect
            && (!seen.contains(target) || target == &entry.path)
        {
            bail!("invalid cached hard link target");
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
    // Deletions deepest-first, then create parents before children.
    for entry in manifest.entries.iter().rev() {
        if matches!(entry.effect, Effect::Missing) {
            remove(&entry.path)?;
        }
    }
    for entry in &manifest.entries {
        let path = &entry.path;
        if matches!(entry.effect, Effect::Missing) {
            continue;
        }
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        match &entry.effect {
            Effect::Missing => (),
            Effect::Directory { .. } => {
                if fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.is_dir()) {
                    remove(path)?;
                }
                fs::create_dir_all(path)?;
            }
            Effect::Symlink { target } => {
                remove(path)?;
                symlink(target, path)?;
            }
            Effect::File {
                source,
                mode,
                replace,
                ..
            } => {
                if Path::new(source).components().count() != 1 {
                    bail!("invalid cached file name");
                }
                if *replace || fs::symlink_metadata(path).is_ok_and(|metadata| !metadata.is_file()) {
                    remove(path)?;
                }
                fs::copy(directory.join(source), path)?;
                fs::set_permissions(path, fs::Permissions::from_mode(*mode))?;
            }
            Effect::HardLink { target } => {
                remove(path)?;
                fs::hard_link(target, path)?;
            }
        }
    }
    // Set directory permissions last so read-only parents don't block child creation.
    for entry in manifest.entries.iter().rev() {
        if let Effect::Directory { mode } = entry.effect {
            fs::set_permissions(&entry.path, fs::Permissions::from_mode(mode))?;
        }
    }
    Ok(())
}

pub(crate) fn exists(directory: &Path) -> bool {
    directory.join(MANIFEST).is_file()
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestDirectory(PathBuf);

    impl Drop for TestDirectory {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    #[test]
    fn replay_preserves_overwrite_and_replacement_alias_semantics() -> Result<()> {
        for replace in [false, true] {
            let fixture =
                TestDirectory(std::env::temp_dir().join(format!("incr-effects-{}", rand::random::<u128>())));
            fs::create_dir(&fixture.0)?;
            let output = fixture.0.join("output");
            let alias = fixture.0.join("alias");
            let replacement = fixture.0.join("replacement");
            let cache = fixture.0.join("cache");
            fs::write(&output, b"old")?;
            fs::hard_link(&output, &alias)?;
            if replace {
                fs::write(&replacement, b"new")?;
                fs::rename(&replacement, &output)?;
            } else {
                fs::write(&output, b"new")?;
            }
            let expected_alias = fs::read(&alias)?;
            let writes = HashSet::from([output.clone()]);
            let replacements = if replace { writes.clone() } else { HashSet::new() };
            capture(&cache, &writes, &replacements)?;

            fs::remove_file(&output)?;
            fs::write(&alias, b"old")?;
            fs::hard_link(&alias, &output)?;
            replay(&cache)?;
            assert_eq!(fs::read(&output)?, b"new");
            assert_eq!(fs::read(&alias)?, expected_alias);
            assert_eq!(
                fs::metadata(&output)?.ino() == fs::metadata(&alias)?.ino(),
                !replace
            );
        }
        Ok(())
    }
}
