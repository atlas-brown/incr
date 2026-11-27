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
    pub(crate) dependency_report_complete: bool,
    /// Why the dependency report is incomplete, as Observe reported it.
    pub(crate) dependency_report_incomplete_reasons: Vec<String>,
    pub(crate) reads: HashSet<PathBuf>,
    pub(crate) writes: HashSet<PathBuf>,
    pub(crate) initial_file_ids: HashMap<PathBuf, (u64, u64)>,
    pub(crate) initial_dependencies: HashMap<PathBuf, crate::cache::DependencyKey>,
}

pub(crate) fn parse_trace(runtime: &Runtime) -> Result<Trace> {
    let trace_file = match &runtime.kind {
        RuntimeType::Sandbox(directory) => directory.join("upperdir").join("tmp").join(TRACE_FILE),
        RuntimeType::TraceFile(file) | RuntimeType::Observe(file) => file.clone(),
        RuntimeType::Nothing => {
            return Ok(Trace {
                dependency_report_complete: true,
                ..Trace::default()
            });
        }
    };
    // eBPF daemon backend: collect this command's events from the daemon and
    // write the observe.json the parser below expects, so the rest is unchanged.
    if let Some(session) = runtime.daemon_session.borrow_mut().take() {
        let options = observe_core::Options {
            hash_writes: true,
            dependencies: true,
            hash_dependencies: false,
            snapshot_dir: runtime.snapshot_directory.clone(),
            detach_executable: None,
            // Daemon-direct path: no entry-stop tracer, so the collector
            // reports unknown pre-write states instead of hashing at drain.
            prestate: false,
            ignore_cache_dependency: crate::config::docker_cache_paths(),
        };
        let mut outcome = session.collect(&options, 0)?;
        outcome.drop_ignored(&options);
        observe_core::report::write(&outcome, Some(&trace_file), true)?;
    }
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

    /// Under FinalOutputs, drop rename-alias barriers on regular files when the
    /// captured outputs hold every name of each hard-linked output.
    pub(crate) fn drop_recorded_alias_barriers(
        &mut self,
        policy: crate::config::EffectPolicy,
        dependencies: &HashMap<PathBuf, crate::cache::DependencyKey>,
    ) {
        let is_alias = |reason: &String| {
            reason.starts_with(RENAME_ALIAS_BARRIER) && reason.contains(" file_type=regular ")
        };
        if policy != crate::config::EffectPolicy::FinalOutputs
            || !self.replay_barriers.iter().any(is_alias)
            || !crate::cache::effects::hard_links_recorded(&self.writes, dependencies)
        {
            return;
        }
        self.replay_barriers.retain(|reason| !is_alias(reason));
    }
}

const RENAME_ALIAS_BARRIER: &str = "rename source inode cannot be replayed without changing aliases:";

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

    #[test]
    fn recorded_alias_barriers_are_dropped_only_under_final_outputs() {
        let directory = std::env::temp_dir().join(format!("incr-alias-{}", rand::random::<u128>()));
        fs::create_dir(&directory).unwrap();
        let (first, second) = (directory.join("first"), directory.join("second"));
        fs::write(&first, b"x").unwrap();
        fs::hard_link(&first, &second).unwrap();
        let alias =
            format!("{RENAME_ALIAS_BARRIER} source=\"a\" destination=\"b\" file_type=regular nlink=2");
        let special =
            format!("{RENAME_ALIAS_BARRIER} source=\"a\" destination=\"b\" file_type=special nlink=2");
        let trace = |writes: &[&PathBuf]| Trace {
            replay_barriers: vec![alias.clone(), special.clone(), "other".to_owned()],
            writes: writes.iter().map(|path| (*path).clone()).collect(),
            ..Default::default()
        };
        let no_dependencies = HashMap::new();

        let mut both = trace(&[&first, &second]);
        both.drop_recorded_alias_barriers(crate::config::EffectPolicy::FinalOutputs, &no_dependencies);
        assert_eq!(both.replay_barriers, vec![special.clone(), "other".to_owned()]);

        let mut one = trace(&[&first]);
        one.drop_recorded_alias_barriers(crate::config::EffectPolicy::FinalOutputs, &no_dependencies);
        assert_eq!(one.replay_barriers.len(), 3);

        let mut live = trace(&[&first, &second]);
        live.drop_recorded_alias_barriers(crate::config::EffectPolicy::Live, &no_dependencies);
        assert_eq!(live.replay_barriers.len(), 3);
        fs::remove_dir_all(&directory).unwrap();
    }
}
