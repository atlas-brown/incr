//! Parse observe's JSON output into (read_set, write_set).

use std::collections::HashSet;
use std::path::{Path, PathBuf};

type Result<T> = std::result::Result<T, String>;

#[derive(serde::Deserialize)]
struct ObserveReport {
    reads: Vec<String>,
    writes: serde_json::Value,
}

/// Parse observe's JSON output and return (read_set, write_set).
/// Handles both plain writes: ["path1", "path2"] and hash format: [{"path": "...", "pre_hash": "..."}].
pub fn parse_observe(trace_path: &Path) -> Result<(HashSet<PathBuf>, HashSet<PathBuf>)> {
    let data = std::fs::read_to_string(trace_path)
        .map_err(|e| format!("read {:?}: {e}", trace_path))?;

    let report: ObserveReport = serde_json::from_str(&data)
        .map_err(|e| format!("parse observe JSON: {e}"))?;

    let read_set: HashSet<PathBuf> = report.reads.into_iter().map(PathBuf::from).collect();

    let write_set: HashSet<PathBuf> = match report.writes {
        serde_json::Value::Array(arr) => {
            let mut writes = HashSet::new();
            for item in arr {
                match item {
                    serde_json::Value::String(s) => {
                        writes.insert(PathBuf::from(s));
                    }
                    serde_json::Value::Object(obj) => {
                        if let Some(serde_json::Value::String(path)) = obj.get("path") {
                            writes.insert(PathBuf::from(path));
                        }
                    }
                    _ => {}
                }
            }
            writes
        }
        _ => HashSet::new(),
    };

    Ok((read_set, write_set))
}
