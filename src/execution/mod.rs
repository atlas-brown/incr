pub(crate) mod batch_executor;
pub(crate) mod chunk_executor;
pub(crate) mod dependency;
pub(crate) mod record;
pub(crate) mod run;
pub(crate) mod skip_executor;
mod speculation;
pub(crate) mod stream_executor;

use anyhow::Result;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

use crate::annotation;
use crate::command::{Command, Runtime, RuntimeType};
use crate::config::{EXCLUDED_PATHS, TRACE_FILE, TraceType};
use crate::scripts;

pub(crate) fn get_trace_type(
    cache_directory: &Path,
    command: &Command,
    observe_command: Option<&str>,
    introspection: bool,
) -> TraceType {
    if annotation::check_pure(command) {
        return TraceType::Nothing;
    }
    if annotation::check_read_only(command) {
        return TraceType::TraceFile;
    }
    // Observe records unexpected writes and arbitrates live effects. strace's
    // read-only fast path cannot safely use a witness from different stdin.
    if introspection
        && observe_command.is_some()
        && dependency::get_introspect_file(cache_directory, command.hash).exists()
    {
        return TraceType::TraceFile;
    }
    // When observe is available, use Observe mode instead of Sandbox (no try overlayfs)
    if observe_command.is_some() {
        return TraceType::Observe;
    }
    TraceType::Sandbox
}

#[derive(Default)]
pub(crate) struct Trace {
    pub(crate) replay_barriers: Vec<String>,
    pub(crate) reads: HashSet<PathBuf>,
    pub(crate) writes: HashSet<PathBuf>,
    pub(crate) initial_file_ids: HashMap<PathBuf, (u64, u64)>,
    pub(crate) initial_dependencies: HashMap<PathBuf, crate::cache::DependencyKey>,
}

pub(crate) fn parse_trace(runtime: &Runtime) -> Result<Trace> {
    let trace_file = match &runtime.kind {
        RuntimeType::Sandbox(directory) => directory.join("upperdir").join("tmp").join(TRACE_FILE),
        RuntimeType::TraceFile(file) | RuntimeType::Observe(file) => file.clone(),
        RuntimeType::Nothing => return Ok(Trace::default()),
    };
    let mut trace = if trace_file
        .extension()
        .is_some_and(|extension| extension == "json")
    {
        scripts::parse_observe(&trace_file)?
    } else {
        scripts::parse_trace(&trace_file)?
    };
    if trace_file.exists() {
        fs::remove_file(&trace_file)?;
    }

    trace.reads.retain(|path| is_tracked_path(path));
    trace.writes.retain(|path| is_tracked_path(path));

    Ok(trace)
}

impl Trace {
    pub(crate) fn apply_effect_policy(&mut self, policy: crate::config::EffectPolicy) {
        if policy == crate::config::EffectPolicy::FinalOutputs {
            self.replay_barriers.retain(|reason| {
                !matches!(
                    reason.as_str(),
                    "rename preserves inode identity" | "unlink may replace an existing inode"
                )
            });
        }
    }
}

/// Traces name absolute filesystem entries; pseudo descriptors are not paths.
fn is_tracked_path(path: &Path) -> bool {
    path.is_absolute() && !EXCLUDED_PATHS.iter().any(|root| path.starts_with(root))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn excluded_roots_match_whole_components() {
        for path in ["/process/input", "/proc-results", "/tmp/quote\"/file"] {
            assert!(is_tracked_path(Path::new(path)), "{path}");
        }
        for path in ["/proc", "/proc/self/fd/4", "pipe:[42]", "relative"] {
            assert!(!is_tracked_path(Path::new(path)), "{path}");
        }
    }
}
