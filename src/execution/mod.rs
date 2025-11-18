pub(crate) mod batch_executor;
pub(crate) mod chunk_executor;
pub(crate) mod dependency;
pub(crate) mod run;
pub(crate) mod skip_executor;
pub(crate) mod stream_executor;

use anyhow::{Result, anyhow};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::annotation;
use crate::command::{Command, Runtime, RuntimeType};
use crate::config::{EXCLUDED_PATHS, TRACE_FILE, TraceType};
use crate::ops;
use crate::scripts;

pub(crate) fn get_trace_type(cache_directory: &Path, command: &Command) -> TraceType {
    if annotation::check_pure(command) {
        return TraceType::Nothing;
    }
    if annotation::check_stateless(command) || annotation::check_read_only(command) {
        return TraceType::TraceFile;
    }
    if dependency::get_introspect_file(cache_directory, command.hash).exists() {
        return TraceType::TraceFile;
    }
    TraceType::Sandbox
}

pub(crate) fn parse_trace(runtime: &Runtime) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    let trace_file = match &runtime.typ {
        RuntimeType::Sandbox(directory) => &directory.join("upperdir").join("tmp").join(TRACE_FILE),
        RuntimeType::TraceFile(file) => file,
        RuntimeType::Nothing => return Ok((HashSet::new(), HashSet::new())),
    };
    let (mut read_set, mut write_set) = scripts::parse_trace(trace_file).map_err(|e| anyhow!("{e}"))?;
    fs::remove_file(trace_file)?;

    read_set.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::file::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });
    write_set.retain(|p| {
        !EXCLUDED_PATHS.iter().any(|e| {
            ops::file::path_to_string(p)
                .map(|p| p.starts_with(e))
                .unwrap_or(true)
        })
    });

    Ok((read_set, write_set))
}
