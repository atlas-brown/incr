//! Decode Observe reports under the selected temporary scratch-state contract.
use crate::cache::DependencyKey;
use crate::config::OBSERVE_READ_EXCLUDED_PATHS;
use crate::execution::Trace;
use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
struct Report {
    dependency_version: u32,
    #[serde(default)]
    directory_access_only: bool,
    #[serde(default)]
    overwrites: Vec<ReportPath>,
    #[serde(default)]
    content_opens: Option<Vec<ReportPath>>,
    replay_barriers: Vec<String>,
    dependencies: Vec<Dependency>,
    reads: Vec<ReportPath>,
    writes: Vec<Write>,
}

#[derive(Deserialize)]
struct ReportPath(#[serde(with = "crate::ops::unix_path")] PathBuf);

#[derive(Deserialize)]
struct Dependency {
    #[serde(with = "crate::ops::unix_path")]
    path: PathBuf,
    #[serde(flatten)]
    state: ObservedDependency,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum ObservedDependency {
    Absent,
    NotDirectory,
    ParentDirectory {
        mode: u32,
        uid: u32,
        gid: u32,
        access: u8,
    },
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
        #[serde(with = "crate::ops::unix_path")]
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
    Path(#[serde(with = "crate::ops::unix_path")] PathBuf),
    Hashed {
        #[serde(with = "crate::ops::unix_path")]
        path: PathBuf,
        pre_hash: Option<String>,
    },
}

pub(crate) fn parse_observe(
    path: &Path,
    track_temporaries: bool,
    assume_directory_access: bool,
    content_validated_inputs: bool,
) -> Result<Trace> {
    let report: Report = serde_json::from_slice(&std::fs::read(path)?)
        .with_context(|| format!("decode Observe report {}", path.display()))?;
    if !matches!(report.dependency_version, 7 | 8 | 9 | 10 | 11)
        || report.directory_access_only != assume_directory_access
        || (report.directory_access_only && !matches!(report.dependency_version, 10 | 11))
        || (content_validated_inputs != (report.dependency_version == 11))
        || (content_validated_inputs != report.content_opens.is_some())
    {
        anyhow::bail!("unsupported Observe dependency protocol");
    }
    let temporary_roots = temporary_roots();
    let tracked = |path: &Path| tracked_path(path, track_temporaries, &temporary_roots);
    let mut trace = Trace {
        replay_barriers: report.replay_barriers,
        ..Trace::default()
    };
    trace.reads.extend(
        report
            .reads
            .into_iter()
            .map(|path| path.0)
            .filter(|path| tracked(path)),
    );
    for path in report.content_opens.into_iter().flatten().map(|path| path.0) {
        if tracked(&path) {
            anyhow::ensure!(trace.reads.contains(&path), "content open is not a reported read");
            trace.content_opens.insert(path);
        }
    }
    for Dependency {
        path,
        state: observed,
    } in report.dependencies
    {
        if !tracked(&path) {
            continue;
        }
        let key = match observed {
            ObservedDependency::Absent => DependencyKey::DoesNotExist,
            ObservedDependency::NotDirectory => DependencyKey::NotDirectory,
            ObservedDependency::ParentDirectory {
                mode,
                uid,
                gid,
                access,
            } => DependencyKey::ParentDirectory {
                mode,
                uid,
                gid,
                access,
            },
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
    trace.overwrites.extend(
        report
            .overwrites
            .into_iter()
            .map(|path| path.0)
            .filter(|path| tracked(path)),
    );
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

fn temporary_roots() -> Vec<PathBuf> {
    let mut roots = vec![PathBuf::from("/tmp"), PathBuf::from("/var/tmp")];
    if let Some(directory) = std::env::var_os("TMPDIR") {
        let path = PathBuf::from(directory);
        // A root TMPDIR must not silently exclude the entire filesystem.
        if path.is_absolute() && path != Path::new("/") {
            if let Ok(resolved) = std::fs::canonicalize(&path) {
                // A symlink or lexical alias of / is also not scratch.
                if resolved == Path::new("/") {
                    return roots;
                }
                roots.push(resolved);
            }
            roots.push(path);
        }
    }
    roots
}

fn tracked_path(path: &Path, track_temporaries: bool, temporary_roots: &[PathBuf]) -> bool {
    path.is_absolute()
        && !OBSERVE_READ_EXCLUDED_PATHS
            .iter()
            .any(|root| path.starts_with(root))
        && (track_temporaries || !temporary_roots.iter().any(|root| path.starts_with(root)))
}

#[cfg(test)]
mod temporary_policy_tests {
    use super::*;

    #[test]
    fn scratch_prefixes_respect_components_and_the_tracking_override() {
        let roots = vec!["/tmp".into(), "/var/tmp".into(), "/work/private-scratch".into()];
        for name in ["/tmp/input", "/var/tmp/output", "/work/private-scratch/result"] {
            assert!(!tracked_path(Path::new(name), false, &roots));
            assert!(tracked_path(Path::new(name), true, &roots));
        }
        for name in [
            "/tmp-data/input",
            "/work/private-scratch-neighbor/input",
            "/work/input",
        ] {
            assert!(tracked_path(Path::new(name), false, &roots));
        }
        for name in ["/proc/self/maps", "/sys/info", "/dev/null", "relative"] {
            assert!(!tracked_path(Path::new(name), true, &roots));
        }
    }
}
