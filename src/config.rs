use std::fmt::{Display, Error as FormatError, Formatter};
use std::path::PathBuf;

pub(crate) const DEFAULT_TRY_PATH: &str = "incr/src/scripts/try.sh";
pub(crate) const STRACE_COMMAND: &str = "strace";
pub(crate) const BASH_COMMAND: &str = "bash";
pub(crate) const DEFAULT_CACHE_PATH: &str = "incr/cache";
pub(crate) const INTROSPECT_DIRECTORY: &str = "introspect";

pub(crate) const DATA_FILE: &str = "data";
pub(crate) const STDOUT_FILE: &str = "stdout.incr";
pub(crate) const STDERR_FILE: &str = "stderr.incr";
pub(crate) const DEBUG_FILE: &str = "debug_info.json";

pub(crate) const TRACE_FILE: &str = "trace.txt";
pub(crate) const OBSERVE_TRACE_FILE: &str = "observe.json";
pub(crate) const SANDBOX_DIRECTORY: &str = "sandbox";
pub(crate) const OUTPUT_DIRECTORY: &str = "outputs";
pub(crate) const COMMIT_DIRECTORY: &str = "commit";

pub(crate) const CHUNK_WORKERS: usize = 4;
pub(crate) const CHUNK_SIZES: ChunkSizes = ChunkSizes {
    minimum: 1_000_000,
    average: 4_000_000,
    maximum: 16_000_000,
};
pub(crate) const CHUNK_GRANULARITY: usize = 16;
pub(crate) const COMPRESSION_LEVEL: i32 = 1;
pub(crate) const BUFFER_SIZE: usize = 65_536;
pub(crate) const PARALLEL_SIZE: usize = 1000;

pub(crate) const SUDO_SANDBOX: bool = true;
pub(crate) const DEBUG: bool = false;
pub(crate) const DEBUG_LOGS: bool = DEBUG && true;
pub(crate) const DEBUG_LOG_PATH: &str = "incr/debug_log.txt";

pub(crate) const EXCLUDED_VARIABLES: &[&str] = &[
    "GIT_ASKPASS",
    "SHLVL",
    "SSH_CLIENT",
    "SSH_CONNECTION",
    "VSCODE_GIT_ASKPASS_EXTRA_ARGS",
    "VSCODE_GIT_ASKPASS_MAIN",
    "VSCODE_GIT_ASKPASS_NODE",
    "VSCODE_GIT_IPC_HANDLE",
    "VSCODE_IPC_HOOK_CLI",
    "VSCODE_PYTHON_AUTOACTIVATE_GUARD",
    "XDG_RUNTIME_DIR",
    "XDG_SESSION_CLASS",
    "XDG_SESSION_ID",
    "XDG_SESSION_TYPE",
    "_",
];
pub(crate) const EXCLUDED_PATHS: &[&str] = &["/proc", "pipe:"];
pub(crate) const DYNAMIC_EXCLUDED_PATHS: &[&str] = &["/tmp"];

/// Paths to exclude from observe-mode read dependencies. Observe runs without sandbox
/// and traces more paths (e.g. /tmp, /dev) that change between runs, causing cache
/// invalidation. Filtering these at parse time improves cache hits for observe mode.
pub(crate) const OBSERVE_READ_EXCLUDED_PATHS: &[&str] = &["/tmp", "/dev", "/proc", "/sys"];

#[derive(Clone, Debug)]
pub(crate) struct Config {
    pub(crate) try_command: String,       // Bash try command string
    pub(crate) cache_directory: PathBuf, // Directory to store cache data
    pub(crate) trace_type: TraceType,    // Type of tracing to use
    pub(crate) observe_command: Option<String>, // Path to observe binary; when Some, use observe for tracing

    pub(crate) batch_executor: bool,     // Run using the batch executor
    pub(crate) short_circuit: bool,      // Exit after a downstream failure
    pub(crate) compress_output: bool,    // Compress stdout and stderr
    pub(crate) full_tracing: bool,       // Run without selective activation
    pub(crate) enable_annotations: bool, // Run with annotations
    pub(crate) skip_introspection: bool, // Disable command introspection
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum TraceType {
    Sandbox,
    TraceFile,
    Observe,
    Nothing,
}

impl Display for TraceType {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> Result<(), FormatError> {
        match self {
            Self::Sandbox => write!(formatter, "Sandbox"),
            Self::TraceFile => write!(formatter, "TraceFile"),
            Self::Observe => write!(formatter, "Observe"),
            Self::Nothing => write!(formatter, "Nothing"),
        }
    }
}

#[derive(Clone, Debug)]
pub(crate) struct ChunkSizes {
    pub(crate) minimum: usize,
    pub(crate) average: usize,
    pub(crate) maximum: usize,
}
