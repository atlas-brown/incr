#[derive(Clone, Debug)]
pub(crate) struct Config {
    pub(crate) skip_sandbox: bool,       // Do not use a try sandbox
    pub(crate) complete_execution: bool, // Complete after a downstream failure
}

#[derive(Clone, Debug)]
pub(crate) struct SkipCondition {
    pub(crate) name: &'static str,
    pub(crate) disallowed_flags: &'static [&'static str],
}

impl SkipCondition {
    const fn without_flags(name: &'static str) -> Self {
        Self {
            name,
            disallowed_flags: &[],
        }
    }

    const fn with_flags(name: &'static str, disallowed_flags: &'static [&'static str]) -> Self {
        Self {
            name,
            disallowed_flags,
        }
    }
}

pub(crate) const TRY_COMMAND: &str = "/users/jxia3/incr/src/scripts/try.sh";
pub(crate) const STRACE_COMMAND: &str = "strace";
pub(crate) const TRACE_FILE: &str = "trace.txt";
pub(crate) const DEBUG_LOG_FILE: &str = "debug_log.txt";

pub(crate) const CACHE_DIRECTORY: &str = "/users/jxia3/incr/cache";
pub(crate) const DATA_FILE: &str = "data";
pub(crate) const SANDBOX_DIRECTORY: &str = "sandbox";
pub(crate) const OUTPUT_DIRECTORY: &str = "outputs";
pub(crate) const COMMIT_DIRECTORY: &str = "commit";
pub(crate) const DEBUG_FILE: &str = "debug_info.json";

pub(crate) const CHUNK_SIZE: usize = 65536;
pub(crate) const SUDO_SANDBOX: bool = true;
pub(crate) const DEBUG: bool = false;
pub(crate) const DEBUG_LOGS: bool = DEBUG && true;

pub(crate) const IGNORE_COMMANDS: &[&str] = &[
    "alias", "cd", "chgrp", "chmod", "chown", "date", "df", "du", "env", "export", "free", "hash",
    "hostname", "id", "ln", "mkdir", "mktmp", "mv", "printenv", "ps", "read", "rm", "rmdir", "set", "sleep",
    "stty", "sync", "time", "top", "touch", "tput", "umask", "uname", "unalias", "uptime", "w", "who",
    "whoami", "yes",
];
pub(crate) const SKIP_COMMANDS: &[&str] = &[
    "basename", "cat", "cut", "dirname", "echo", "false", "head", "ls", "paste", "printf", "pwd", "rev",
    "seq", "stat", "tail", "tee", "test", "tr", "true", "type", "which", "xargs",
];
pub(crate) const SKIP_SANDBOX_CONDITIONS: &[SkipCondition] = &[
    SkipCondition::without_flags("awk"),
    SkipCondition::without_flags("comm"),
    SkipCondition::without_flags("cmp"),
    SkipCondition::without_flags("diff"),
    SkipCondition::without_flags("grep"),
    SkipCondition::without_flags("join"),
    SkipCondition::with_flags("sort", &["-o", "--output"]),
    SkipCondition::with_flags("uniq", &["-o", "--output"]),
    SkipCondition::without_flags("wc"),
];

pub(crate) const EXCLUDED_VARIABLES: &[&str] = &[
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
