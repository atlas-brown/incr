use anyhow::{Result, anyhow};
use bincode::Encode;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, BufWriter, Error as IoError, ErrorKind, Read, Write};
use std::iter;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::os::unix::process::CommandExt;
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
        iter::once(self.name.as_str()).chain(self.arguments.iter().map(|a| a.as_str()))
    }
}

#[derive(Clone, Debug, Encode)]
struct CommandKey<'c> {
    name: &'c str,
    arguments: &'c [String],
    environment: &'c BTreeMap<String, String>,
    executable: Option<ExecutableState>,
}

#[derive(Clone, Debug, Encode)]
struct ExecutableState {
    path: PathBuf,
    dev: u64,
    ino: u64,
    changed_sec: i64,
    changed_nsec: i64,
    modified_sec: i64,
    modified_nsec: i64,
    size: u64,
    mode: u32,
}

#[derive(Clone, Debug)]
pub(crate) struct Runtime {
    pub(crate) typ: RuntimeType,
    pub(crate) stdout_file: PathBuf,
    pub(crate) stderr_file: PathBuf,
    pub(crate) effect_gate: Option<std::sync::Arc<crate::effect_gate::EffectGate>>,
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
    pub(crate) child: Child,
    pub(crate) stdout_thread: JoinHandle<Result<ChildResult>>,
    pub(crate) stderr_thread: JoinHandle<Result<ChildResult>>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum ChildResult {
    Completed(usize),
    BrokenPipe,
}

pub(crate) fn create(mut arguments: Vec<String>, environment: &HashMap<String, String>) -> Result<Command> {
    assert!(!arguments.is_empty());
    if arguments.len() == 1 {
        let command_string = arguments.pop().unwrap();
        arguments = shlex::split(&command_string).ok_or_else(|| anyhow!("Could not split command"))?
    }
    if arguments.is_empty() {
        return Err(anyhow!("Empty command"));
    }
    let name = arguments.remove(0);

    let excluded_variables = EXCLUDED_VARIABLES.iter().copied().collect::<HashSet<_>>();
    let mut environment = environment
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

    environment.insert(
        "PWD".into(),
        std::env::current_dir()?.to_string_lossy().into_owned(),
    );

    let executable = executable_state(&name, &environment);
    let standard_tool = executable.as_ref().is_some_and(|state| {
        ["/usr/bin", "/bin"].iter().any(|directory| {
            fs::canonicalize(Path::new(directory).join(&name)).ok().as_ref() == Some(&state.path)
        })
    });
    let key_data = ops::data::encode_to_bytes(&CommandKey {
        name: &name,
        arguments: &arguments,
        environment: &environment,
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
        let Ok(m) = fs::metadata(&path) else { continue };
        if !m.is_file() {
            continue;
        }
        return Some(ExecutableState {
            path,
            dev: m.dev(),
            ino: m.ino(),
            changed_sec: m.ctime(),
            changed_nsec: m.ctime_nsec(),
            modified_sec: m.mtime(),
            modified_nsec: m.mtime_nsec(),
            size: m.len(),
            mode: m.mode(),
        });
    }
    None
}

/// Extra inherited descriptors carry state/communication outside the stdin
/// cache key. Do not memoize them. Ignore Rust's own close-on-exec handles.
fn has_inherited_descriptors() -> Result<bool> {
    for entry in fs::read_dir("/proc/self/fd")? {
        let entry = entry?;
        let Some(fd) = entry.file_name().to_str().and_then(|s| s.parse::<i32>().ok()) else {
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
    if let RuntimeType::Sandbox(directory) = &runtime.typ {
        fs::create_dir_all(directory)?;
    } else if let RuntimeType::TraceFile(file) | RuntimeType::Observe(file) = &runtime.typ
        && let Some(parent) = file.parent()
    {
        fs::create_dir_all(parent)?;
    }

    let mut child = spawn_child(config, command, runtime)?;
    let mut child_stdout = child.stdout.take().unwrap();
    let mut child_stderr = child.stderr.take().unwrap();
    let config = config.clone();
    let destination_ready = destination_ready.clone();

    let stdout_thread = thread::spawn({
        let config = config.clone();
        let stdout_file = runtime.stdout_file.clone();
        let destination_ready = destination_ready.clone();
        move || {
            capture_stream(
                &config,
                &mut child_stdout,
                &mut io::stdout(),
                &stdout_file,
                &destination_ready,
            )
        }
    });
    let stderr_thread = thread::spawn({
        let stderr_file = runtime.stderr_file.clone();
        move || {
            capture_stream(
                &config,
                &mut child_stderr,
                &mut io::stderr(),
                &stderr_file,
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
    let shell_command = match &runtime.typ {
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

    match &runtime.typ {
        RuntimeType::Sandbox(directory) => {
            child.env("TRY_IGNORE_FILE", directory.join(".ignore.pending"));
            child.arg("-D");
            child.arg(ops::file::path_to_string(directory)?);
            child.arg(STRACE_COMMAND);
            child.arg("-yf");
            child.arg("--seccomp-bpf");
            child.arg("--trace=fork,clone,%file");
            child.arg("-o");
            child.arg(format!("/tmp/{TRACE_FILE}"));
            child.arg(&command.name);
            child.args(&command.arguments);
        }
        RuntimeType::TraceFile(file) => {
            if use_observe {
                child.arg("--json");
                child.arg("--hash");
                child.arg("--dependencies");
                child.arg("--output");
                child.arg(ops::file::path_to_string(file)?);
                child.arg("--no-filter");
                child.arg("--");
                child.arg(&command.name);
                child.args(&command.arguments);
            } else {
                let mut arguments = vec![
                    "-yf",
                    "--seccomp-bpf",
                    "--trace=fork,clone,%file",
                    "-o",
                    ops::file::path_to_string(file)?,
                ];
                arguments.extend(command.join_sequence());
                child.args(&arguments);
            }
        }
        RuntimeType::Observe(file) => {
            child.arg("--json");
            child.arg("--hash");
            child.arg("--dependencies");
            child.arg("--output");
            child.arg(ops::file::path_to_string(file)?);
            child.arg("--no-filter");
            child.arg("--");
            child.arg(&command.name);
            child.args(&command.arguments);
        }
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

fn capture_stream<S, D, R>(
    config: &Config,
    source: &mut S,
    destination: &mut D,
    capture_file: &Path,
    destination_ready: &R,
) -> Result<ChildResult>
where
    S: Read,
    D: Write,
    R: ReadySignal,
{
    if let Some(parent) = capture_file.parent() {
        fs::create_dir_all(parent)?;
    }
    let file = File::create(capture_file)?;
    let mut file_writer = BufWriter::with_capacity(BUFFER_SIZE, file);

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
    let mut pending = Vec::new();
    let mut destination_broken = false;
    let mut length = 0;

    loop {
        let count = match source.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };

        if !destination_ready.check_ready() {
            pending.extend_from_slice(&chunk[..count]);
            continue;
        }
        let outputs = if pending.is_empty() {
            &[&chunk[..count]] as &[_]
        } else {
            &[&pending, &chunk[..count]]
        };

        for output in outputs {
            if !destination_broken && let Err(error) = destination.write_all(output) {
                if error.kind() != ErrorKind::BrokenPipe {
                    return Err(error.into());
                }
                destination_broken = true;
            }
            stream.write_all(output)?;
            length += output.len();
            if destination_broken && config.short_circuit {
                return Ok(ChildResult::BrokenPipe);
            }
        }
        pending.clear();
    }

    if !pending.is_empty() {
        assert!(!destination_broken && length == 0);
        destination_ready.wait_until_ready();
        if let Err(error) = destination.write_all(&pending) {
            if error.kind() != ErrorKind::BrokenPipe {
                return Err(error.into());
            }
            destination_broken = true;
        }
        stream.write_all(&pending)?;
        length += pending.len();
        if destination_broken && config.short_circuit {
            return Ok(ChildResult::BrokenPipe);
        }
    }

    Ok(ChildResult::Completed(length))
}

pub(crate) fn kill_child(child: &Child) -> Result<()> {
    let group_id = child.id() as i32;
    let kill_result = unsafe { libc::kill(-group_id, libc::SIGKILL) };
    if kill_result == -1 {
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
        for pid in children.split_whitespace().filter_map(|p| p.parse::<i32>().ok()) {
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
