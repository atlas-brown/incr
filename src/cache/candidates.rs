//! Pre-execution validation for final-output streaming replay.
use anyhow::Result;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

const MAX_CANDIDATES: usize = 8;
const MAX_INDEX_ENTRIES: usize = 64;

use super::{CacheData, batch_cache::CacheCursor};
use crate::{
    command::Command,
    config::{Config, EffectPolicy},
    execution::dependency,
};

pub(crate) struct Candidate<'a> {
    pub(crate) stdin_hash: u64,
    pub(crate) cache: CacheCursor<'a>,
    pub(crate) data: CacheData,
}

pub(crate) fn validate<'a>(config: &Config, command: &'a Command) -> Result<Vec<Candidate<'a>>> {
    if config.observe_command.is_none() || config.effect_policy != EffectPolicy::FinalOutputs {
        return Ok(Vec::new());
    }
    let directory = config
        .cache_directory
        .join("candidates")
        .join(command.hash.to_string());
    let keys = recent_entries(&directory);
    let mut candidates = Vec::new();
    for (_, stdin_hash, _) in keys.into_iter().take(MAX_CANDIDATES) {
        let cache = CacheCursor::from_hash(config, command, stdin_hash)?;
        if let Some(data) = cache.load_data()?
            && dependency::check_cache_valid(&cache, &data)?
        {
            candidates.push(Candidate {
                stdin_hash,
                cache,
                data,
            });
        }
    }
    Ok(candidates)
}

fn recent_entries(directory: &Path) -> Vec<(SystemTime, u64, PathBuf)> {
    let Ok(entries) = fs::read_dir(directory) else {
        return Vec::new();
    };
    let mut keys: Vec<_> = entries
        .filter_map(|entry| {
            let entry = entry.ok()?;
            if !entry.file_type().ok()?.is_file() {
                return None;
            }
            Some((
                entry.metadata().ok()?.modified().ok()?,
                entry.file_name().to_str()?.parse::<u64>().ok()?,
                entry.path(),
            ))
        })
        .collect();
    keys.sort_unstable_by(|left, right| right.cmp(left));
    keys
}

pub(crate) fn record(directory: &Path, stdin_hash: u64) {
    // The index is only a hint; concurrent pruning may lose hits, never validity.
    if fs::create_dir_all(directory).is_err()
        || fs::write(directory.join(stdin_hash.to_string()), []).is_err()
    {
        return;
    }
    for (_, _, path) in recent_entries(directory).into_iter().skip(MAX_INDEX_ENTRIES) {
        let _ = fs::remove_file(path);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn index_retention_ignores_unrelated_entries() -> Result<()> {
        let directory = std::env::temp_dir().join(format!("incr-index-{}", rand::random::<u128>()));
        fs::create_dir(&directory)?;
        let result = (|| -> Result<()> {
            fs::write(directory.join("unrelated"), b"keep")?;
            fs::create_dir(directory.join("1234"))?;
            for stdin_hash in 0..100 {
                record(&directory, stdin_hash);
            }
            assert_eq!(recent_entries(&directory).len(), MAX_INDEX_ENTRIES);
            assert!(directory.join("99").is_file());
            assert_eq!(fs::read(directory.join("unrelated"))?, b"keep");
            assert!(directory.join("1234").is_dir());
            Ok(())
        })();
        fs::remove_dir_all(directory)?;
        result
    }
}
