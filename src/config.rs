#[derive(Clone, Debug)]
pub struct Config {
    pub complete_after_downstream_failure: bool,
}

pub const TRY_COMMAND: &str = "./src/try.sh";
pub const STRACE_COMMAND: &str = "strace";
pub const TRACE_FILE: &str = "trace.txt";

pub const CACHE_DIRECTORY: &str = "cache";
pub const DATA_FILE: &str = "data";
pub const SANDBOX_DIRECTORY: &str = "sandbox";
pub const OUTPUT_DIRECTORY: &str = "outputs";
pub const COMMIT_DIRECTORY: &str = "commit";
pub const DEBUG_FILE: &str = "debug_info.json";

pub const CHUNK_SIZE: usize = 65536;
pub const SUDO_SANDBOX: bool = true;
pub const DEBUG: bool = false;

pub const EXCLUDED_VARS: &[&str] = &[
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
pub const EXCLUDED_PATHS: &[&str] = &[
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
