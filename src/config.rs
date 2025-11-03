use std::fmt::{Display, Error as FormatError, Formatter};
use std::path::PathBuf;

#[derive(Clone, Debug)]
pub(crate) struct Config {
    pub(crate) complete_execution: bool, // Complete after a downstream failure
    pub(crate) compress: bool,           // Whether to compress cached outputs
    pub(crate) force_cache: bool,        // Do not skip the command
    pub(crate) try_command: String,      // Bash try command string
    pub(crate) cache_directory: PathBuf, // Directory to store cache data
    pub(crate) trace_type: TraceType,    // Type of tracing to use
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TraceType {
    Sandbox,
    TraceFile,
    Nothing,
}

impl Display for TraceType {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> Result<(), FormatError> {
        match self {
            Self::Sandbox => write!(formatter, "Sandbox"),
            Self::TraceFile => write!(formatter, "TraceFile"),
            Self::Nothing => write!(formatter, "Nothing"),
        }
    }
}

#[derive(Clone, Debug)]
pub(crate) struct SkipCondition {
    pub(crate) name: &'static str,
    pub(crate) disallowed_flags: &'static [&'static str],
    pub(crate) max_arguments: usize,
    pub(crate) max_input: usize,
}

impl SkipCondition {
    #[allow(unused)]
    const fn with_name(name: &'static str) -> Self {
        Self {
            name,
            disallowed_flags: &[],
            max_arguments: usize::MAX,
            max_input: usize::MAX,
        }
    }

    #[allow(unused)]
    const fn with_disallowed_flags(name: &'static str, disallowed_flags: &'static [&'static str]) -> Self {
        Self {
            name,
            disallowed_flags,
            max_arguments: usize::MAX,
            max_input: usize::MAX,
        }
    }

    #[allow(unused)]
    const fn with_conditions(
        name: &'static str,
        disallowed_flags: &'static [&'static str],
        max_arguments: usize,
        max_input: usize,
    ) -> Self {
        Self {
            name,
            disallowed_flags,
            max_arguments,
            max_input,
        }
    }
}

pub(crate) const DEFAULT_TRY_PATH: &str = "incr/src/scripts/try.sh";
pub(crate) const STRACE_COMMAND: &str = "strace";
pub(crate) const BASH_COMMAND: &str = "bash";
pub(crate) const DEFAULT_CACHE_PATH: &str = "incr/cache";

pub(crate) const DATA_FILE: &str = "data";
pub(crate) const STDOUT_FILE: &str = "stdout.incr";
pub(crate) const STDERR_FILE: &str = "stderr.incr";
pub(crate) const DEBUG_FILE: &str = "debug_info.json";

pub(crate) const TRACE_FILE: &str = "trace.txt";
pub(crate) const SANDBOX_DIRECTORY: &str = "sandbox";
pub(crate) const OUTPUT_DIRECTORY: &str = "outputs";
pub(crate) const COMMIT_DIRECTORY: &str = "commit";

pub(crate) const CHUNK_SIZE: usize = 65536;
pub(crate) const COMPRESSION_LEVEL: i32 = 1;
pub(crate) const SUDO_SANDBOX: bool = true;
pub(crate) const DEBUG: bool = true;
pub(crate) const DEBUG_LOGS: bool = DEBUG && true;
pub(crate) const DEBUG_LOG_FILE: &str = "/users/jxia3/incr/debug_log.txt";

pub(crate) const IGNORE_COMMANDS: &[&str] = &[
    "alias", "break", "cd", "chgrp", "chmod", "chown", "continue", "env", "export", "ln", "printenv", "pwd",
    "set", "sleep", "stty", "sync", "tput", "umask", "unalias", "yes",
];
pub(crate) const SKIP_COMMANDS: &[&str] = &[];
pub(crate) const SKIP_CACHE_CONDITIONS: &[SkipCondition] = &[];
pub(crate) const SKIP_TRACE_CONDITIONS: &[SkipCondition] = &[];
pub(crate) const SKIP_SANDBOX_CONDITIONS: &[SkipCondition] = &[];

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
