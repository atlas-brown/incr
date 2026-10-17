//! Strict decoding of Observe reports. Ordinary /tmp files remain dependencies.
use crate::cache::DependencyKey;
use crate::config::OBSERVE_READ_EXCLUDED_PATHS;
use crate::execution::Trace;
use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
struct Report {
    dependency_version: u32,
    dependency_report_complete: bool,
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
        uid: u32,
        gid: u32,
        access: Option<u8>,
        content_hash: Option<u64>,
    },
    Directory {
        modified: u64,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
        uid: u32,
        gid: u32,
        access: Option<u8>,
        entry_hash: Option<u64>,
    },
    Symlink {
        #[serde(with = "crate::ops::unix_path")]
        target: PathBuf,
        modified: u64,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
        uid: u32,
        gid: u32,
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

pub(crate) fn parse_observe(path: &Path) -> Result<Trace> {
    let docker_dependency_report = std::env::var_os("INCR_DOCKER_DEPENDENCY_REPORT").is_some();
    parse_observe_with_mode(path, docker_dependency_report)
}

fn parse_observe_with_mode(path: &Path, docker_dependency_report: bool) -> Result<Trace> {
    let report: Report = serde_json::from_slice(&std::fs::read(path)?)
        .with_context(|| format!("decode Observe report {}", path.display()))?;
    if report.dependency_version != 10 {
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
        dependency_report_complete: report.dependency_report_complete,
        ..Trace::default()
    };
    trace.reads.extend(
        report
            .reads
            .into_iter()
            .map(|path| path.0)
            .filter(|path| tracked(path)),
    );
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
                uid,
                gid,
                access,
                content_hash,
            } => {
                trace.initial_file_ids.insert(path.clone(), (device, inode));
                if let Some(hash) = content_hash {
                    match access {
                        Some(access) => DependencyKey::ContentState {
                            modified: modified.into(),
                            size,
                            mode,
                            uid,
                            gid,
                            access,
                            hash,
                        },
                        None => DependencyKey::Uncacheable,
                    }
                } else {
                    DependencyKey::FileState {
                        modified: modified.into(),
                        changed_sec,
                        changed_nsec,
                        size,
                        mode,
                    }
                }
            }
            ObservedDependency::Directory {
                modified: _,
                mode,
                uid,
                gid,
                access,
                entry_hash,
                ..
            } if docker_dependency_report => match entry_hash {
                Some(entry_hash) => DependencyKey::DockerDirectoryState {
                    entry_hash,
                    mode,
                    uid,
                    gid,
                    access: access.ok_or_else(|| {
                        anyhow::anyhow!("Docker directory dependency is missing access state")
                    })?,
                },
                None => DependencyKey::Uncacheable,
            },
            ObservedDependency::Directory {
                modified,
                changed_sec,
                changed_nsec,
                mode,
                ..
            } => DependencyKey::DirectoryState {
                modified: modified.into(),
                changed_sec,
                changed_nsec,
                mode,
            },
            ObservedDependency::Symlink {
                target,
                modified,
                changed_sec: _,
                changed_nsec: _,
                mode,
                uid,
                gid,
                ..
            } if docker_dependency_report => DependencyKey::DockerSymlinkState {
                target,
                modified: modified.into(),
                mode,
                uid,
                gid,
            },
            ObservedDependency::Symlink {
                target,
                modified,
                changed_sec,
                changed_nsec,
                mode,
                ..
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_dependency_report_completeness() {
        let path = std::env::temp_dir().join(format!(
            "incr-observe-report-{}-{}.json",
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::write(
            &path,
            r#"{"dependency_version":10,"dependency_report_complete":true,"replay_barriers":["uncapturable-output"],"dependencies":[],"reads":[],"writes":[]}"#,
        )
        .unwrap();

        let trace = parse_observe(&path).unwrap();
        std::fs::remove_file(path).unwrap();

        assert!(trace.dependency_report_complete);
        assert_eq!(trace.replay_barriers, vec!["uncapturable-output".to_owned()]);
    }

    #[test]
    fn parses_hashed_dependencies_and_docker_metadata_keys() {
        let path = std::env::temp_dir().join(format!(
            "incr-observe-report-{}-{}.json",
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::write(
            &path,
            r#"{"dependency_version":10,"dependency_report_complete":true,"replay_barriers":[],"dependencies":[{"path":"/input","kind":"file","device":2,"inode":3,"modified":4,"changed_sec":5,"changed_nsec":6,"size":7,"mode":33188,"uid":1,"gid":2,"access":7,"content_hash":8},{"path":"/directory","kind":"directory","modified":9,"changed_sec":10,"changed_nsec":11,"mode":16877,"uid":1,"gid":2,"access":7,"entry_hash":15},{"path":"/link","kind":"symlink","target":"/target","modified":12,"changed_sec":13,"changed_nsec":14,"mode":41471,"uid":1,"gid":2}],"reads":[],"writes":[]}"#,
        )
        .unwrap();

        let trace = parse_observe_with_mode(&path, true).unwrap();
        std::fs::remove_file(path).unwrap();

        assert!(matches!(
            trace.initial_dependencies.get(Path::new("/input")),
            Some(DependencyKey::ContentState { hash: 8, .. })
        ));
        assert!(matches!(
            trace.initial_dependencies.get(Path::new("/directory")),
            Some(DependencyKey::DockerDirectoryState { .. })
        ));
        assert!(matches!(
            trace.initial_dependencies.get(Path::new("/link")),
            Some(DependencyKey::DockerSymlinkState { .. })
        ));
        assert_eq!(trace.initial_file_ids.get(Path::new("/input")), Some(&(2, 3)));
    }

    #[test]
    fn keeps_strict_metadata_keys_outside_docker_mode() {
        let path = std::env::temp_dir().join(format!(
            "incr-observe-report-{}-{}.json",
            std::process::id(),
            rand::random::<u64>()
        ));
        std::fs::write(
            &path,
            r#"{"dependency_version":10,"dependency_report_complete":true,"replay_barriers":[],"dependencies":[{"path":"/directory","kind":"directory","modified":9,"changed_sec":10,"changed_nsec":11,"mode":16877,"uid":1,"gid":2,"access":null,"entry_hash":null}],"reads":[],"writes":[]}"#,
        )
        .unwrap();

        let trace = parse_observe_with_mode(&path, false).unwrap();
        std::fs::remove_file(path).unwrap();

        assert!(matches!(
            trace.initial_dependencies.get(Path::new("/directory")),
            Some(DependencyKey::DirectoryState { changed_sec: 10, .. })
        ));
    }
}
