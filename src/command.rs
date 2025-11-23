use anyhow::{Result, anyhow};
use bincode::Encode;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::ffi::{OsStr, OsString};
use std::fs::{self, File};
use std::io::{self, BufWriter, Error as IoError, ErrorKind, Read, Write};
use std::os::unix::ffi::{OsStrExt, OsStringExt};
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
    pub(crate) arguments: Vec<OsString>,
    pub(crate) environment: BTreeMap<String, String>,
    pub(crate) hash: u64,
}

impl Command {
    pub(crate) fn join_string(&self) -> Result<OsString> {
        build_shell_command(&self.name, &self.arguments)
    }

    pub(crate) fn argument_bytes(&self) -> Vec<Vec<u8>> {
        to_bytes(&self.arguments)
    }

    pub(crate) fn argument_strings(&self) -> Vec<String> {
        self.arguments
            .iter()
            .map(|argument| argument.to_string_lossy().into_owned())
            .collect()
    }
}

#[derive(Clone, Debug, Encode)]
struct CommandKey<'c> {
    name: &'c str,
    arguments: &'c [Vec<u8>],
    environment: &'c BTreeMap<String, String>,
}

#[derive(Clone, Debug)]
pub(crate) struct Runtime {
    pub(crate) typ: RuntimeType,
    pub(crate) stdout_file: PathBuf,
    pub(crate) stderr_file: PathBuf,
}

#[derive(Clone, Debug)]
pub(crate) enum RuntimeType {
    Sandbox(PathBuf),
    TraceFile(PathBuf),
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

pub(crate) fn create(mut arguments: Vec<OsString>, environment: &HashMap<String, String>) -> Result<Command> {
    assert!(!arguments.is_empty());
    if arguments.len() == 1 {
        let command_string = arguments
            .pop()
            .unwrap()
            .into_string()
            .map_err(|_| anyhow!("Commands provided as a single string must be valid UTF-8"))?;
        arguments = shlex::split(&command_string)
            .ok_or_else(|| anyhow!("Could not split command"))?
            .into_iter()
            .map(OsString::from)
            .collect();
    }
    let name = arguments
        .remove(0)
        .into_string()
        .map_err(|_| anyhow!("Command name must be valid UTF-8"))?;

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

    let argument_bytes = to_bytes(&arguments);
    let key_data = ops::data::encode_to_bytes(&CommandKey {
        name: &name,
        arguments: &argument_bytes,
        environment: &environment,
    })?;
    let hash = ops::data::hash_bytes(&key_data);

    Ok(Command {
        name,
        arguments,
        environment,
        hash,
    })
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
    } else if let RuntimeType::TraceFile(file) = &runtime.typ
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
    let shell_command = match &runtime.typ {
        RuntimeType::Sandbox(_) => &config.try_command,
        RuntimeType::TraceFile(_) => STRACE_COMMAND,
        RuntimeType::Nothing => &command.name,
    };
    let mut child = ShellCommand::new(shell_command);

    match &runtime.typ {
        RuntimeType::Sandbox(directory) => {
            let sandbox_directory = ops::file::path_to_string(directory)?;
            let trace_destination = format!("/tmp/{TRACE_FILE}");
            let command_string = command.join_string()?;
            child
                .arg("-D")
                .arg(sandbox_directory)
                .arg(STRACE_COMMAND)
                .arg("-yf")
                .arg("--seccomp-bpf")
                .arg("--trace=fork,clone,%file")
                .arg("-o")
                .arg(trace_destination)
                .arg(command_string);
        }
        RuntimeType::TraceFile(file) => {
            let trace_output = ops::file::path_to_string(file)?;
            child
                .arg("-yf")
                .arg("--seccomp-bpf")
                .arg("--trace=fork,clone,%file")
                .arg("-o")
                .arg(trace_output)
                .arg(&command.name)
                .args(&command.arguments);
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

fn to_bytes(arguments: &[OsString]) -> Vec<Vec<u8>> {
    arguments.iter().map(|arg| arg.as_bytes().to_vec()).collect()
}

fn build_shell_command(name: &str, arguments: &[OsString]) -> Result<OsString> {
    let mut components = Vec::with_capacity(arguments.len() + 1);
    components.push(shell_escape(OsStr::new(name)));
    for argument in arguments {
        components.push(shell_escape(argument.as_os_str()));
    }
    let total_len = components.iter().map(|component| component.len()).sum::<usize>()
        + components.len().saturating_sub(1);
    let mut bytes = Vec::with_capacity(total_len);
    for (index, component) in components.into_iter().enumerate() {
        if index > 0 {
            bytes.push(b' ');
        }
        bytes.extend_from_slice(&component);
    }
    Ok(OsString::from_vec(bytes))
}

fn shell_escape(argument: &OsStr) -> Vec<u8> {
    let bytes = argument.as_bytes();
    if bytes.is_empty() {
        return b"''".to_vec();
    }
    let mut escaped = Vec::with_capacity(bytes.len() + 2);
    escaped.push(b'\'');
    for &byte in bytes {
        if byte == b'\'' {
            escaped.extend_from_slice(b"'\\''");
        } else {
            escaped.push(byte);
        }
    }
    escaped.push(b'\'');
    escaped
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
