use anyhow::{Result, anyhow};
use bincode::Encode;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, BufWriter, Error as IoError, ErrorKind, Read, Write};
use std::iter;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::os::unix::process::{CommandExt, ExitStatusExt};
use std::path::{Path, PathBuf};
use std::process::{Child, Command as ShellCommand, Stdio};
use std::thread::{self, JoinHandle};
use zstd::Encoder;

use crate::config::{BUFFER_SIZE, COMPRESSION_LEVEL, Config, EXCLUDED_VARIABLES, STRACE_COMMAND, TRACE_FILE};
use crate::ops;
use crate::ops::thread::{AlwaysReady, ReadySignal};

#[derive(Clone, Debug)]
pub(crate) struct Command {
    pub(crate) name: String,
    pub(crate) arguments: Vec<String>,
    pub(crate) environment: BTreeMap<String, String>,
    pub(crate) hash: u64,
    pub(crate) inherited_descriptors: bool,
    pub(crate) standard_tool: bool,
}

impl Command {
    pub(crate) fn join_string(&self) -> Result<String> {
        Ok(shlex::try_join(self.join_sequence())?)
    }

    pub(crate) fn join_sequence(&self) -> impl Iterator<Item = &str> {
        iter::once(self.name.as_str()).chain(self.arguments.iter().map(String::as_str))
    }
}

#[derive(Clone, Debug, Encode)]
struct CommandKey<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    working_directory: &'c [u8],
    executable: Option<ExecutableState>,
}

#[derive(Clone, Debug, Encode)]
struct ExecutableState {
    path_bytes: Vec<u8>,
    device: u64,
    inode: u64,
    changed_sec: i64,
    changed_nsec: i64,
    modified_sec: i64,
    modified_nsec: i64,
    size: u64,
    mode: u32,
}

#[derive(Clone, Debug)]
pub(crate) struct Runtime {
    pub(crate) kind: RuntimeType,
    pub(crate) stdout_file: PathBuf,
    pub(crate) stderr_file: PathBuf,
    pub(crate) effect_gate: Option<std::sync::Arc<crate::effect_gate::EffectGate>>,
    pub(crate) snapshot_directory: Option<PathBuf>,
}

#[derive(Clone, Debug)]
pub(crate) enum RuntimeType {
    Sandbox(PathBuf),
    TraceFile(PathBuf),
    Observe(PathBuf),
    Nothing,
}

#[derive(Debug)]
pub(crate) struct ChildContext {
    pub(crate) child: ManagedChild,
    pub(crate) stdout_thread: JoinHandle<Result<ChildResult>>,
    pub(crate) stderr_thread: JoinHandle<Result<ChildResult>>,
}

#[derive(Debug)]
pub(crate) struct ManagedChild(Child);

impl std::ops::Deref for ManagedChild {
    type Target = Child;
    fn deref(&self) -> &Child {
        &self.0
    }
}

impl std::ops::DerefMut for ManagedChild {
    fn deref_mut(&mut self) -> &mut Child {
        &mut self.0
    }
}

impl Drop for ManagedChild {
    fn drop(&mut self) {
        if matches!(self.0.try_wait(), Ok(Some(_))) {
            return;
        }
        let _ = kill_child(&self.0);
        let deadline = std::time::Instant::now() + std::time::Duration::from_millis(250);
        while matches!(self.0.try_wait(), Ok(None)) && std::time::Instant::now() < deadline {
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum ChildResult {
    Completed { length: usize, broken_pipe: bool },
    BrokenPipe,
}

/// Preserve the caller's argument boundaries and fingerprint execution inputs.
pub(crate) fn create(arguments: Vec<String>, environment: &HashMap<String, String>) -> Result<Command> {
    let mut arguments = arguments.into_iter();
    let name = arguments.next().ok_or_else(|| anyhow!("Empty command"))?;
    let arguments: Vec<_> = arguments.collect();

    let excluded_variables = EXCLUDED_VARIABLES.iter().copied().collect::<HashSet<_>>();
    let environment = environment
        .iter()
        .filter_map(|(variable, value)| {
            if !excluded_variables.contains(variable.as_str())
                && (!variable.starts_with("BASH_FUNC_") || !variable.ends_with("%%"))
            {
                Some((variable.clone(), value.clone()))
            } else {
                None
            }
        })
        .collect::<BTreeMap<_, _>>();

    let working_directory = std::env::current_dir()?;

    let executable = executable_state(&name, &environment);
    let standard_tool = executable.as_ref().is_some_and(|state| {
        ["/usr/bin", "/bin"].iter().any(|directory| {
            fs::canonicalize(Path::new(directory).join(&name))
                .is_ok_and(|path| path.as_os_str().as_bytes() == state.path_bytes)
        })
    });
    let key_data = ops::data::encode_to_bytes(&CommandKey {
        name: &name,
        arguments: &arguments,
        environment: &environment,
        working_directory: working_directory.as_os_str().as_bytes(),
        executable,
    })?;
    let hash = ops::data::hash_bytes(&key_data);

    Ok(Command {
        name,
        arguments,
        environment,
        hash,
        inherited_descriptors: has_inherited_descriptors()?,
        standard_tool,
    })
}

// Resolve the executable using execvp's search order. Static annotations only
// describe the installed system tools, not arbitrary programs with their names.
fn executable_state(name: &str, environment: &BTreeMap<String, String>) -> Option<ExecutableState> {
    let candidates = if name.contains('/') {
        vec![PathBuf::from(name)]
    } else {
        std::env::split_paths(environment.get("PATH").map_or("/bin:/usr/bin", String::as_str))
            .map(|directory| directory.join(name))
            .collect()
    };
    for candidate in candidates {
        let Ok(c_path) = std::ffi::CString::new(candidate.as_os_str().as_bytes()) else {
            continue;
        };
        if unsafe { libc::access(c_path.as_ptr(), libc::X_OK) } != 0 {
            continue;
        }
        let Ok(path) = fs::canonicalize(candidate) else {
            continue;
        };
        let Ok(metadata) = fs::metadata(&path) else {
            continue;
        };
        if !metadata.is_file() {
            continue;
        }
        return Some(ExecutableState {
            path_bytes: path.as_os_str().as_bytes().to_vec(),
            device: metadata.dev(),
            inode: metadata.ino(),
            changed_sec: metadata.ctime(),
            changed_nsec: metadata.ctime_nsec(),
            modified_sec: metadata.mtime(),
            modified_nsec: metadata.mtime_nsec(),
            size: metadata.len(),
            mode: metadata.mode(),
        });
    }
    None
}

/// Extra inherited descriptors carry state/communication outside the stdin
/// cache key. Do not memoize them. Ignore Rust's own close-on-exec handles.
fn has_inherited_descriptors() -> Result<bool> {
    for entry in fs::read_dir("/proc/self/fd")? {
        let entry = entry?;
        let Some(fd) = entry
            .file_name()
            .to_str()
            .and_then(|name| name.parse::<i32>().ok())
        else {
            continue;
        };
        if fd <= 2 {
            continue;
        }
        let flags = unsafe { libc::fcntl(fd, libc::F_GETFD) };
        if flags >= 0 && flags & libc::FD_CLOEXEC == 0 {
            return Ok(true);
        }
    }
    Ok(false)
}

pub(crate) fn spawn(config: &Config, command: &Command, runtime: &Runtime) -> Result<ChildContext> {
    spawn_with_signal(config, command, runtime, &AlwaysReady)
}

pub(crate) fn spawn_with_signal<R>(
    config: &Config,
    command: &Command,
    runtime: &Runtime,
    destination_ready: &R,
) -> Result<ChildContext>
where
    R: Clone + ReadySignal + Send + 'static,
{
    if let RuntimeType::Sandbox(directory) = &runtime.kind {
        fs::create_dir_all(directory)?;
    } else if let RuntimeType::TraceFile(file) | RuntimeType::Observe(file) = &runtime.kind
        && let Some(parent) = file.parent()
    {
        fs::create_dir_all(parent)?;
    }

    let stdout_capture = create_capture_file(&runtime.stdout_file)?;
    let stderr_capture = create_capture_file(&runtime.stderr_file)?;
    let mut child = ManagedChild(spawn_child(config, command, runtime)?);
    let mut child_stdout = child.stdout.take().unwrap();
    let mut child_stderr = child.stderr.take().unwrap();
    let config = config.clone();
    let destination_ready = destination_ready.clone();

    let stdout_thread = thread::spawn({
        let config = config.clone();
        let destination_ready = destination_ready.clone();
        move || {
            capture_stream(
                &config,
                &mut child_stdout,
                &mut io::stdout(),
                stdout_capture,
                &destination_ready,
            )
        }
    });
    let stderr_thread = thread::spawn({
        move || {
            capture_stream(
                &config,
                &mut child_stderr,
                &mut io::stderr(),
                stderr_capture,
                &destination_ready,
            )
        }
    });

    Ok(ChildContext {
        child,
        stdout_thread,
        stderr_thread,
    })
}

fn spawn_child(config: &Config, command: &Command, runtime: &Runtime) -> Result<Child> {
    let use_observe = config.observe_command.is_some();
    let shell_command = match &runtime.kind {
        RuntimeType::Sandbox(_) => &config.try_command,
        RuntimeType::TraceFile(_) => {
            if use_observe {
                config.observe_command.as_ref().unwrap()
            } else {
                STRACE_COMMAND
            }
        }
        RuntimeType::Observe(_) => config.observe_command.as_ref().unwrap(),
        RuntimeType::Nothing => &command.name,
    };
    let mut child = ShellCommand::new(shell_command);
    if let Some(gate) = &runtime.effect_gate {
        child.arg("--effect-gate").arg(&gate.path);
    }
    if let Some(directory) = &runtime.snapshot_directory {
        child.arg("--snapshot-dir").arg(directory);
        child
            .arg("--snapshot-exclude")
            .arg(directory.join("exclude.json"));
    }

    match &runtime.kind {
        RuntimeType::Sandbox(directory) => {
            child.env("TRY_IGNORE_FILE", directory.join(".ignore.pending"));
            child.arg("-D");
            child.arg(ops::file::path_to_string(directory)?);
            child.arg(STRACE_COMMAND);
            child.args(["-yf", "-s", "4096"]);
            child.arg("--seccomp-bpf");
            child.arg("--trace=fork,vfork,clone,clone3,%file");
            child.arg("-o");
            child.arg(format!("/tmp/{TRACE_FILE}"));
            child.arg(&command.name);
            child.args(&command.arguments);
        }
        RuntimeType::TraceFile(file) | RuntimeType::Observe(file) if use_observe => {
            child.args(["--json", "--hash", "--dependencies", "--output"]);
            child.arg(file);
            child.args(["--no-filter", "--"]);
            child.arg(&command.name).args(&command.arguments);
        }
        RuntimeType::TraceFile(file) => {
            child.args([
                "-yf",
                "-s",
                "4096",
                "--seccomp-bpf",
                "--trace=fork,vfork,clone,clone3,%file",
                "-o",
            ]);
            child.arg(file);
            child.arg(&command.name).args(&command.arguments);
        }
        RuntimeType::Observe(_) => anyhow::bail!("Observe runtime requires an Observe executable"),
        RuntimeType::Nothing => {
            child.args(&command.arguments);
        }
    };

    child
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    unsafe {
        child.pre_exec(|| {
            // A dead owner must not leave a gate-blocked tracer behind.
            if libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGKILL) == -1 {
                return Err(IoError::last_os_error());
            }
            if libc::setpgid(0, 0) == -1 {
                Err(IoError::last_os_error())
            } else {
                Ok(())
            }
        });
    }

    Ok(child.spawn()?)
}

fn create_capture_file(path: &Path) -> Result<File> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    Ok(File::create(path)?)
}

fn capture_stream<S, D, R>(
    config: &Config,
    source: &mut S,
    destination: &mut D,
    capture_file: File,
    destination_ready: &R,
) -> Result<ChildResult>
where
    S: Read,
    D: Write,
    R: ReadySignal,
{
    let mut file_writer = BufWriter::with_capacity(BUFFER_SIZE, capture_file);

    if !config.compress_output {
        let output = capture_into_stream(config, source, destination, &mut file_writer, destination_ready);
        file_writer.flush()?;
        output
    } else {
        let mut compressor = Encoder::new(file_writer, COMPRESSION_LEVEL)?;
        let output = capture_into_stream(config, source, destination, &mut compressor, destination_ready);
        compressor.finish()?.flush()?;
        output
    }
}

fn capture_into_stream<S, D, W, R>(
    config: &Config,
    source: &mut S,
    destination: &mut D,
    stream: &mut W,
    destination_ready: &R,
) -> Result<ChildResult>
where
    S: Read,
    D: Write,
    W: Write,
    R: ReadySignal,
{
    let mut chunk = [0; BUFFER_SIZE];
    let mut pending = None;
    let mut destination_broken = false;
    let mut length = 0;

    loop {
        let count = match source.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        stream.write_all(&chunk[..count])?;
        if !destination_ready.check_ready() {
            let pending = pending.get_or_insert_with(|| PendingOutput::new(&config.cache_directory));
            pending.sender.send(&chunk[..count])?;
            pending.length += count;
            continue;
        }
        if let Some(pending) = pending.take() {
            length += pending.length;
            destination_broken = pending.forward(destination)?;
        }
        if !destination_broken && let Err(error) = destination.write_all(&chunk[..count]) {
            if error.kind() != ErrorKind::BrokenPipe {
                return Err(error.into());
            }
            destination_broken = true;
        }
        length += count;
        if destination_broken && config.short_circuit {
            return Ok(ChildResult::BrokenPipe);
        }
    }
    if let Some(pending) = pending {
        destination_ready.wait_until_ready();
        length += pending.length;
        destination_broken = pending.forward(destination)?;
        if destination_broken && config.short_circuit {
            return Ok(ChildResult::BrokenPipe);
        }
    }

    Ok(ChildResult::Completed {
        length,
        broken_pipe: destination_broken,
    })
}

struct PendingOutput {
    sender: ops::spool::Sender,
    receiver: ops::spool::Receiver,
    length: usize,
}

impl PendingOutput {
    fn new(directory: &Path) -> Self {
        let (sender, receiver) = ops::spool::create(directory);
        Self {
            sender,
            receiver,
            length: 0,
        }
    }

    fn forward(self, destination: &mut impl Write) -> Result<bool> {
        drop(self.sender);
        Ok(self.receiver.forward(destination)? == crate::ops::stream::TransferOutcome::BrokenPipe)
    }
}

pub(crate) fn restore_snapshot(observe: &str, directory: &Path) -> Result<()> {
    let mut child = ManagedChild(
        ShellCommand::new(observe)
            .arg("revert")
            .arg(directory)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .process_group(0)
            .spawn()?,
    );
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
    loop {
        if let Some(status) = child.try_wait()? {
            anyhow::ensure!(
                status.success(),
                "cannot restore speculative filesystem effects: {status}"
            );
            return Ok(());
        }
        anyhow::ensure!(
            std::time::Instant::now() < deadline,
            "snapshot restoration exceeded its deadline"
        );
        thread::sleep(std::time::Duration::from_millis(1));
    }
}

pub(crate) fn exit_code(status: std::process::ExitStatus) -> i32 {
    status
        .code()
        .unwrap_or_else(|| 128 + status.signal().unwrap_or(0))
}

pub(crate) fn kill_child(child: &Child) -> Result<()> {
    let group_id = child.id() as i32;
    let kill_result = unsafe { libc::kill(-group_id, libc::SIGKILL) };
    if kill_result == -1 && IoError::last_os_error().raw_os_error() != Some(libc::ESRCH) {
        Err(IoError::last_os_error().into())
    } else {
        Ok(())
    }
}

/// All execution threads have finished. Reap adopted descendants left by a
/// cancelled tracer instead of leaving zombies to the host's init process.
pub(crate) fn reap_children() {
    let children_path = format!("/proc/self/task/{}/children", std::process::id());
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(1);
    loop {
        let mut status = 0;
        while unsafe { libc::waitpid(-1, &mut status, libc::WNOHANG) } > 0 {}
        let children = fs::read_to_string(&children_path).unwrap_or_default();
        if children.trim().is_empty() {
            break;
        }
        for pid in children
            .split_whitespace()
            .filter_map(|pid| pid.parse::<i32>().ok())
        {
            unsafe {
                libc::kill(pid, libc::SIGKILL);
            }
        }
        if std::time::Instant::now() >= deadline {
            break;
        }
        std::thread::sleep(std::time::Duration::from_millis(1));
    }
}

/// Stop Observe, allowing its termination handler to stop/reap all tracees and
/// persist the partial dependency report before any cached effects are installed.
pub(crate) fn stop_observed_child(child: &mut Child) -> Result<()> {
    if child.try_wait()?.is_none() {
        if unsafe { libc::kill(child.id() as i32, libc::SIGTERM) } != 0 {
            return Err(IoError::last_os_error().into());
        }
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(1);
        while child.try_wait()?.is_none() {
            if std::time::Instant::now() >= deadline {
                kill_child(child)?;
                child.wait()?;
                reap_children();
                anyhow::bail!("Observe did not stop within the replay deadline");
            }
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
    }
    reap_children();
    let children = fs::read_to_string(format!("/proc/self/task/{}/children", std::process::id()))?;
    if !children.trim().is_empty() {
        anyhow::bail!("refusing replay while child processes remain");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dropping_running_child_stops_and_reaps_it() -> Result<()> {
        let child = ShellCommand::new("sleep").arg("30").process_group(0).spawn()?;
        let process_id = child.id() as i32;
        drop(ManagedChild(child));
        let mut status = 0;
        assert_eq!(
            unsafe { libc::waitpid(process_id, &mut status, libc::WNOHANG) },
            -1
        );
        assert_eq!(IoError::last_os_error().raw_os_error(), Some(libc::ECHILD));
        Ok(())
    }
}
