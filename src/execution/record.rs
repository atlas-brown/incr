use anyhow::Result;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::fd::AsRawFd;
use std::os::unix::fs::MetadataExt;

use crate::cache::{CacheData, batch_cache::CacheCursor};
use crate::command::{Runtime, RuntimeType};
use crate::config::Config;
use crate::execution::{self, dependency};
use crate::ops::debug_log;

#[derive(serde::Serialize)]
struct OuterDependencies {
    complete: bool,
    paths: Vec<String>,
}

pub(crate) fn write_outer_dependencies(cache_data: &CacheData) -> Result<()> {
    let Some(report_path) = std::env::var_os("INCR_DOCKER_DEPENDENCY_REPORT") else {
        return Ok(());
    };
    let mut paths = Vec::with_capacity(cache_data.read_dependencies.len());
    let mut complete = cache_data.is_reusable();
    for path in cache_data.read_dependencies.keys() {
        if let Some(path) = path.to_str() {
            paths.push(path.to_owned());
        } else {
            complete = false;
        }
    }
    paths.sort_unstable();
    let mut record = serde_json::to_vec(&OuterDependencies { complete, paths })?;
    record.push(b'\n');

    let mut report = OpenOptions::new().create(true).append(true).open(report_path)?;
    let fd = report.as_raw_fd();
    if unsafe { libc::flock(fd, libc::LOCK_EX) } != 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    let result = report.write_all(&record);
    let unlock = unsafe { libc::flock(fd, libc::LOCK_UN) };
    result?;
    if unlock != 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    Ok(())
}

pub(crate) fn capture(
    config: &Config,
    cache: &CacheCursor<'_>,
    runtime: &Runtime,
    exit_code: i32,
) -> Result<CacheData> {
    let mut trace = execution::parse_trace(runtime)?;
    trace.apply_effect_policy(config.effect_policy);
    let mut read_dependencies = if config.observe_command.is_some() {
        trace
            .reads
            .iter()
            .chain(trace.writes.iter())
            .map(|path| {
                (
                    path.clone(),
                    trace.initial_dependencies.get(path).cloned().unwrap_or_else(|| {
                        if path.ancestors().skip(1).any(|parent| {
                            matches!(
                                trace.initial_dependencies.get(parent),
                                Some(crate::cache::DependencyKey::DoesNotExist)
                            )
                        }) {
                            crate::cache::DependencyKey::DoesNotExist
                        } else {
                            crate::cache::DependencyKey::Uncacheable
                        }
                    }),
                )
            })
            .collect()
    } else {
        dependency::get_read_dependencies(&trace.reads, &trace.writes)?
    };
    if std::env::var_os("INCR_DEBUG_CACHE").is_some() && !trace.replay_barriers.is_empty() {
        eprintln!(
            "[incr] command cache: recording replay barriers: {:?}",
            trace.replay_barriers
        );
    }
    let replaced_paths = trace
        .writes
        .iter()
        .filter(|path| {
            fs::symlink_metadata(path).is_ok_and(|metadata| {
                metadata.is_file()
                    && trace.initial_file_ids.get(*path) != Some(&(metadata.dev(), metadata.ino()))
            })
        })
        .cloned()
        .collect();
    let mut write_set = trace.writes;
    match &runtime.kind {
        RuntimeType::Sandbox(directory) => {
            cache.extract_sandbox_output_from(directory)?;
            if !write_set.is_empty() {
                cache.commit_output()?;
            }
        }
        RuntimeType::Observe(_) | RuntimeType::TraceFile(_) if config.observe_command.is_some() => {
            if trace.replay_barriers.is_empty()
                && let Err(error) = cache.capture_observe_output(&write_set, &replaced_paths)
            {
                debug_log!("Cannot capture output for reuse: {error:#}");
                trace.replay_barriers.push("uncapturable-output".to_owned());
            }
            // Live effects are already applied; capture them without replaying.
        }
        _ => {}
    }
    if config.observe_command.is_none() {
        dependency::filter_dependencies(&mut read_dependencies, &mut write_set)?;
    }

    let cache_data = CacheData {
        replay_barriers: trace.replay_barriers,
        exit_code,
        read_dependencies,
        write_outputs: write_set,
        compressed_output: config.compress_output,
    };

    for (source, destination) in [
        (&runtime.stdout_file, cache.get_stdout_file()),
        (&runtime.stderr_file, cache.get_stderr_file()),
    ] {
        if source != &destination {
            fs::rename(source, destination)?;
        }
    }
    Ok(cache_data)
}
