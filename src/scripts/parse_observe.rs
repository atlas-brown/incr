//! Strict decoding of Observe reports. Ordinary /tmp files remain dependencies.
use crate::cache::DependencyKey;
use crate::config::OBSERVE_READ_EXCLUDED_PATHS;
use crate::execution::Trace;
use anyhow::{Context, Result};
use serde::Deserialize;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
struct Report {
    dependency_version: u32,
    replay_barriers: Vec<String>,
    dependencies: HashMap<PathBuf, ObservedDependency>,
    reads: Vec<PathBuf>,
    writes: Vec<Write>,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum ObservedDependency {
    Absent,
    File {
        device: u64,
        inode: u64,
        modified: u64,
        changed_sec: i64,
        changed_nsec: i64,
        size: u64,
        mode: u32,
    },
    Directory {
        modified: u64,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
    },
    Symlink {
        target: PathBuf,
        modified: u64,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
    },
    Uncacheable,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum Write {
    Path(PathBuf),
    Hashed { path: PathBuf, pre_hash: Option<String> },
}

pub(crate) fn parse_observe(path: &Path) -> Result<Trace> {
    let report: Report = serde_json::from_slice(&std::fs::read(path)?)
        .with_context(|| format!("decode Observe report {}", path.display()))?;
    if report.dependency_version != 5 {
        anyhow::bail!("unsupported Observe dependency protocol");
    }
    let tracked = |path: &Path| {
        path.is_absolute()
            && !OBSERVE_READ_EXCLUDED_PATHS
                .iter()
                .any(|root| path.starts_with(root))
    };
    let mut trace = Trace {
        replay_barriers: report.replay_barriers,
        ..Trace::default()
    };
    trace
        .reads
        .extend(report.reads.into_iter().filter(|path| tracked(path)));
    for (path, observed) in report.dependencies {
        if !tracked(&path) {
            continue;
        }
        let key = match observed {
            ObservedDependency::Absent => DependencyKey::DoesNotExist,
            ObservedDependency::File {
                device,
                inode,
                modified,
                changed_sec,
                changed_nsec,
                size,
                mode,
            } => {
                trace.initial_file_ids.insert(path.clone(), (device, inode));
                DependencyKey::FileState {
                    modified: modified.into(),
                    changed_sec,
                    changed_nsec,
                    size,
                    mode,
                }
            }
            ObservedDependency::Directory {
                modified,
                changed_sec,
                changed_nsec,
                mode,
            } => DependencyKey::DirectoryState {
                modified: modified.into(),
                changed_sec,
                changed_nsec,
                mode,
            },
            ObservedDependency::Symlink {
                target,
                modified,
                changed_sec,
                changed_nsec,
                mode,
            } => DependencyKey::SymlinkState {
                target,
                modified: modified.into(),
                changed_sec,
                changed_nsec,
                mode,
            },
            ObservedDependency::Uncacheable => DependencyKey::Uncacheable,
        };
        trace.initial_dependencies.insert(path, key);
    }
    for write in report.writes {
        let (path, hash) = match write {
            Write::Path(path) => (path, None),
            Write::Hashed { path, pre_hash } => (path, pre_hash),
        };
        if !tracked(&path) {
            continue;
        }
        if let Some(hash) = hash {
            let key = match hash.as_str() {
                "nonexistent" => DependencyKey::DoesNotExist,
                "unreadable" => DependencyKey::Uncacheable,
                hexadecimal => DependencyKey::Hash(
                    u64::from_str_radix(hexadecimal, 16).context("invalid pre-write hash")?,
                ),
            };
            let key = match trace.initial_dependencies.remove(&path) {
                Some(initial) => DependencyKey::All(vec![initial, key]),
                None => key,
            };
            trace.initial_dependencies.insert(path.clone(), key);
        }
        trace.writes.insert(path);
    }
    Ok(trace)
}
