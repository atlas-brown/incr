pub(crate) mod chunk;
pub(crate) mod data;
pub(crate) mod file;
pub(crate) mod serialize_bytes;
pub(crate) mod spool;
pub(crate) mod thread;

use std::env;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::sync::{Mutex, OnceLock};
use time::format_description::FormatItem;
use time::macros::format_description;
use time::{OffsetDateTime, UtcOffset};

use crate::config::{DEBUG_LOG_PATH, DEBUG_LOGS};

pub(crate) const SUCCESS_CODE: ExitCode = ExitCode(0);
pub(crate) const FAILURE_CODE: ExitCode = ExitCode(1);
pub(crate) const BROKEN_PIPE_CODE: ExitCode = ExitCode(141);

const TIME_FORMAT: &[FormatItem<'_>] = format_description!("[hour]:[minute]:[second].[subsecond digits:3]");

macro_rules! debug_log {
    ($($arg:tt)*) => {
        if $crate::config::DEBUG_LOGS {
            let line = format!($($arg)*);
            $crate::ops::log_line(&line);
        }
    };
}

pub(crate) use debug_log;

static LOG_FILE: OnceLock<Mutex<File>> = OnceLock::new();

#[derive(Clone, Debug)]
pub(crate) struct ExitCode(pub(crate) i32);

pub(crate) fn initialize_log_file() {
    if DEBUG_LOGS {
        let Some(directory) = env::home_dir() else { return };
        let path = directory.join(DEBUG_LOG_PATH);
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        if let Ok(file) = OpenOptions::new().append(true).create(true).open(path) {
            let _ = LOG_FILE.set(Mutex::new(file));
        }
    }
}

pub(crate) fn log_line(line: &str) {
    let offset = UtcOffset::current_local_offset().unwrap_or(UtcOffset::UTC);
    let timestamp = OffsetDateTime::now_utc()
        .to_offset(offset)
        .format(&TIME_FORMAT)
        .unwrap();
    let line = format!("[{timestamp}] {line}\n");
    if let Some(file) = LOG_FILE.get()
        && let Ok(mut file) = file.lock()
    {
        let _ = file.write_all(line.as_bytes());
    }
}
