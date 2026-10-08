use anyhow::Result;
use std::fs;
use std::os::unix::fs::MetadataExt;

use crate::cache::{CacheData, batch_cache::CacheCursor};
use crate::command::{Runtime, RuntimeType};
use crate::config::Config;
use crate::execution::{self, dependency};
use crate::ops::debug_log;

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
