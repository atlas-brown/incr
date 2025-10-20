use std::fmt::{Display, Error as FormatError, Formatter};

#[derive(Clone, Debug)]
pub(crate) struct Config {
    pub(crate) force_cache: bool,        // Do not skip the command
    pub(crate) trace_type: TraceType,    // Type of tracing to use
    pub(crate) complete_execution: bool, // Complete after a downstream failure
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
    const fn with_name(name: &'static str) -> Self {
        Self {
            name,
            disallowed_flags: &[],
            max_arguments: usize::MAX,
            max_input: usize::MAX,
        }
    }

    const fn with_disallowed_flags(name: &'static str, disallowed_flags: &'static [&'static str]) -> Self {
        Self {
            name,
            disallowed_flags,
            max_arguments: usize::MAX,
            max_input: usize::MAX,
        }
    }

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
pub(crate) const DEFAULT_CACHE_PATH: &str = "incr/cache";

pub(crate) const BASH_COMMAND: &str = "bash";
pub(crate) const STRACE_COMMAND: &str = "strace";
pub(crate) const TRACE_FILE: &str = "trace.txt";
pub(crate) const DEBUG_FILE: &str = "debug_info.json";

pub(crate) const DATA_FILE: &str = "data";
pub(crate) const SANDBOX_DIRECTORY: &str = "sandbox";
pub(crate) const OUTPUT_DIRECTORY: &str = "outputs";
pub(crate) const COMMIT_DIRECTORY: &str = "commit";

pub(crate) const CHUNK_SIZE: usize = 65536;
pub(crate) const SUDO_SANDBOX: bool = true;
pub(crate) const DEBUG: bool = false;
pub(crate) const DEBUG_LOGS: bool = DEBUG && true;
pub(crate) const DEBUG_LOG_FILE: &str = "/users/jxia3/incr/debug_log.txt";

pub(crate) const IGNORE_COMMANDS: &[&str] = &[
    "alias", "cd", "chgrp", "chmod", "chown", "cp", "date", "df", "du", "env", "export", "free", "hash",
    "hostname", "id", "install", "ln", "ls", "mkdir", "mktemp", "mv", "printenv", "ps", "pwd", "read", "rm",
    "rmdir", "set", "sleep", "stty", "sync", "time", "top", "touch", "tput", "type", "umask", "unalias",
    "uname", "uptime", "w", "which", "who", "whoami", "yes",
];
pub(crate) const SKIP_COMMANDS: &[&str] = &[
    "basename", "cat", "dirname", "echo", "false", "head", "paste", "printf", "rev", "seq", "stat", "tail",
    "tee", "test", "tr", "true", "xargs",
];
pub(crate) const SKIP_SANDBOX_CONDITIONS: &[SkipCondition] = &[
    SkipCondition::with_name("awk"),
    SkipCondition::with_name("cmp"),
    SkipCondition::with_name("comm"),
    SkipCondition::with_name("cut"),
    SkipCondition::with_name("diff"),
    SkipCondition::with_name("grep"),
    SkipCondition::with_name("join"),
    SkipCondition::with_disallowed_flags("sort", &["o", "output"]),
    SkipCondition::with_disallowed_flags("uniq", &["o", "output"]),
    SkipCondition::with_name("wc"),
];
pub(crate) const SKIP_TRACE_CONDITIONS: &[SkipCondition] = &[];
pub(crate) const SKIP_CACHE_CONDITIONS: &[SkipCondition] = &[
    SkipCondition::with_conditions("sort", &[], 0, 200),
    SkipCondition::with_conditions("uniq", &[], 0, 200),
];

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
pub(crate) const EXCLUDED_PATHS: &[&str] = &[
    "/lib/glibc-hwcaps",
    "/lib/tls",
    "/lib/x86_64",
    "/lib/x86_64-linux-gnu",
    "/proc",
    "/tmp",
    "/usr/lib/glibc-hwcaps",
    "/usr/lib/python",
    "/usr/lib/tls",
    "/usr/lib/x86_64",
    "/usr/lib/x86_64-linux-gnu",
    "pipe:",
];
