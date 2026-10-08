//! Roll back speculative filesystem effects before installing a selected cache entry.
use anyhow::Result;
use std::fs;
use std::io::ErrorKind;

use crate::cache::CacheData;
use crate::command::{self, Runtime};
use crate::config::Config;
use crate::execution;

/// Stop and reap the traced process tree, then restore paths outside cached outputs.
/// The caller must have observed the live-effect handshake. On failure, retain any
/// snapshot as `.recovery` and return an error; cached outputs must not be installed.
pub(super) fn stop_and_restore(
    config: &Config,
    runtime: &Runtime,
    child: &mut command::ManagedChild,
    data: &CacheData,
) -> Result<()> {
    // Attachment and the first effect prove Observe's termination handler
    // is active. Before attachment, signalling can lose the report.
    let restoration = (|| -> Result<()> {
        command::stop_observed_child(child)?;
        let mut trace = execution::parse_trace(runtime)?;
        trace.apply_effect_policy(config.effect_policy);
        anyhow::ensure!(
            trace.replay_barriers.is_empty(),
            "speculative execution performed unsupported effects: {:?}",
            trace.replay_barriers
        );
        let restored = restore_speculative_snapshot(config, runtime)?;
        cleanup_speculative_paths(&trace, data, &restored)
    })();
    if let Err(error) = restoration {
        if let Some(directory) = &runtime.snapshot_directory
            && directory.is_dir()
        {
            let recovery = directory.with_extension("recovery");
            fs::rename(directory, &recovery)?;
            return Err(error.context(format!("recovery snapshot retained at {}", recovery.display())));
        }
        return Err(error);
    }
    Ok(())
}

#[derive(serde::Deserialize)]
struct SnapshotManifest {
    entries: Vec<SnapshotEntry>,
    #[serde(default)]
    aliases: Vec<SnapshotAlias>,
}

#[derive(serde::Deserialize)]
struct SnapshotAlias {
    #[serde(with = "crate::ops::unix_path")]
    path: std::path::PathBuf,
    #[serde(with = "crate::ops::unix_path")]
    target: std::path::PathBuf,
}

#[derive(serde::Deserialize)]
struct SnapshotEntry {
    #[serde(with = "crate::ops::unix_path")]
    path: std::path::PathBuf,
}

fn restore_speculative_snapshot(
    config: &Config,
    runtime: &Runtime,
) -> Result<std::collections::HashSet<std::path::PathBuf>> {
    let Some(directory) = &runtime.snapshot_directory else {
        return Ok(std::collections::HashSet::new());
    };
    let manifest: SnapshotManifest = serde_json::from_slice(&fs::read(directory.join("manifest.json"))?)?;
    let mut restored: std::collections::HashSet<_> =
        manifest.entries.into_iter().map(|entry| entry.path).collect();
    let observe = config
        .observe_command
        .as_deref()
        .ok_or_else(|| anyhow::anyhow!("snapshot restoration requires Observe"))?;
    // Even an empty snapshot can contain capture failures that must be checked.
    command::restore_snapshot(observe, directory)?;
    let aliases: Vec<_> = manifest
        .aliases
        .into_iter()
        .filter(|alias| restored.contains(&alias.target))
        .map(|alias| alias.path)
        .collect();
    restored.extend(aliases);
    Ok(restored)
}

fn cleanup_speculative_paths(
    trace: &execution::Trace,
    cached: &CacheData,
    restored: &std::collections::HashSet<std::path::PathBuf>,
) -> Result<()> {
    use crate::cache::DependencyKey;
    fn absent(key: &DependencyKey) -> bool {
        match key {
            DependencyKey::DoesNotExist => true,
            DependencyKey::All(keys) => keys.iter().any(absent),
            _ => false,
        }
    }
    let mut extra: Vec<_> = trace.writes.difference(&cached.write_outputs).collect();
    extra.sort_by_key(|path| std::cmp::Reverse(path.components().count()));
    for path in extra {
        if restored.contains(path) {
            continue;
        }
        if !trace.initial_dependencies.get(path).is_some_and(absent) {
            anyhow::bail!(
                "unexpected speculative write to preexisting path: {}",
                path.display()
            );
        }
        match fs::symlink_metadata(path) {
            Ok(metadata) if metadata.is_dir() => fs::remove_dir(path)?,
            Ok(_) => fs::remove_file(path)?,
            Err(error) if error.kind() == ErrorKind::NotFound => (),
            Err(error) => return Err(error.into()),
        }
    }
    Ok(())
}
