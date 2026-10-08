pub(crate) mod batch_executor;
pub(crate) mod chunk_executor;
pub(crate) mod dependency;
pub(crate) mod run;
pub(crate) mod skip_executor;
pub(crate) mod stream_executor;

use anyhow::{Result, anyhow};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

use crate::annotation;
use crate::command::{Command, Runtime, RuntimeType};
use crate::config::{EXCLUDED_PATHS, TRACE_FILE, TraceType};
use crate::ops;
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
    if annotation::check_stateless(command) || annotation::check_read_only(command) {
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
    pub(crate) initial_dependencies: HashMap<PathBuf, crate::cache::DependencyKey>,
}

pub(crate) fn parse_trace(runtime: &Runtime) -> Result<Trace> {
    let trace_file = match &runtime.typ {
        RuntimeType::Sandbox(directory) => directory.join("upperdir").join("tmp").join(TRACE_FILE),
        RuntimeType::TraceFile(file) | RuntimeType::Observe(file) => file.clone(),
        RuntimeType::Nothing => return Ok(Trace::default()),
    };
    let mut trace = if trace_file.extension().is_some_and(|e| e == "json") {
        scripts::parse_observe(&trace_file)?
    } else {
        let (reads, writes) = scripts::parse_trace(&trace_file).map_err(|e| anyhow!("{e}"))?;
        Trace {
            reads,
            writes,
            ..Trace::default()
        }
    };
    if trace_file.exists() {
        fs::remove_file(&trace_file)?;
    }

    trace.reads.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::file::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });
    trace.writes.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::file::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });

    Ok(trace)
}
