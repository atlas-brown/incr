use anyhow::{Result, anyhow, ensure};
use bincode::Encode;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, BufWriter, Error as IoError, ErrorKind, Read, Write};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command as ShellCommand, Stdio};
use std::thread::{self, JoinHandle};

use crate::config::{BASH_COMMAND, CHUNK_SIZE, Config, EXCLUDED_VARIABLES, STRACE_COMMAND, TRACE_FILE};
use crate::ops;

#[derive(Clone, Debug, Encode)]
pub(crate) struct Command {
    pub(crate) try_command: String,
    pub(crate) cache_directory: String,
    pub(crate) name: String,
    pub(crate) arguments: Vec<String>,
    pub(crate) environment: BTreeMap<String, String>,
}

impl Command {
    pub(crate) fn format_bash(&self) -> Result<String> {
        let mut parts = Vec::with_capacity(self.arguments.len() + 1);
        parts.push(self.name.as_str());
        parts.extend(self.arguments.iter().map(|a| a.as_str()));
        Ok(shlex::try_join(parts)?)
    }
}

#[derive(Clone, Debug)]
pub(crate) struct ChildEnv {
    pub(crate) typ: EnvType,
    pub(crate) stdout_file: PathBuf,
    pub(crate) stderr_file: PathBuf,
}

#[derive(Clone, Debug)]
pub(crate) enum EnvType {
    Sandbox(PathBuf),
    TraceFile(PathBuf),
    Nothing,
}

#[derive(Debug)]
pub(crate) struct ChildContext {
    pub(crate) child: Child,
    pub(crate) stdout_thread: JoinHandle<Result<ChildOutput>>,
    pub(crate) stderr_thread: JoinHandle<Result<ChildOutput>>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ChildOutput {
    Completed(usize),
    BrokenPipe,
}

pub(crate) fn get_command(
    try_command: String,
    cache_directory: String,
    mut arguments: Vec<String>,
    environment: &HashMap<String, String>,
) -> Result<Command> {
    ensure!(!arguments.is_empty());
    if arguments.len() == 1 {
        let command_string = arguments.pop().unwrap();
        arguments = shlex::split(&command_string).ok_or(anyhow!("Could not split command"))?
    }
    let name = arguments.remove(0);

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

    Ok(Command {
        try_command,
        cache_directory,
        name,
        arguments,
        environment,
    })
}

pub(crate) fn spawn_command(config: &Config, command: &Command, env: &ChildEnv) -> Result<ChildContext> {
    if let EnvType::Sandbox(directory) = &env.typ {
        fs::create_dir_all(directory)?;
    }
    let mut child = spawn_child(command, env)?;
    let mut child_stdout = child.stdout.take().unwrap();
    let mut child_stderr = child.stderr.take().unwrap();

    let stdout_thread = thread::spawn({
        let config = config.clone();
        let stdout_file = env.stdout_file.clone();
        move || capture_stream(&config, &mut child_stdout, &mut io::stdout(), &stdout_file)
    });
    let stderr_thread = thread::spawn({
        let config = config.clone();
        let stderr_file = env.stderr_file.clone();
        move || capture_stream(&config, &mut child_stderr, &mut io::stderr(), &stderr_file)
    });

    Ok(ChildContext {
        child,
        stdout_thread,
        stderr_thread,
    })
}

fn spawn_child(command: &Command, env: &ChildEnv) -> Result<Child> {
    let mut command_parts = Vec::with_capacity(command.arguments.len() + 1);
    command_parts.push(command.name.as_str());
    command_parts.extend(command.arguments.iter().map(|a| a.as_str()));
    let command_string = shlex::try_join(command_parts)?;

    let shell_command = match &env.typ {
        EnvType::Sandbox(_) => &command.try_command,
        EnvType::TraceFile(_) => STRACE_COMMAND,
        EnvType::Nothing => BASH_COMMAND,
    };
    let arguments = match &env.typ {
        EnvType::Sandbox(directory) => &[
            "-D",
            ops::path_to_string(directory)?,
            STRACE_COMMAND,
            "-yf",
            "--seccomp-bpf",
            "--trace=fork,clone,%file",
            "-o",
            &format!("/tmp/{TRACE_FILE}"),
            &command_string,
        ] as &[&str],
        EnvType::TraceFile(file) => &[
            "-yf",
            "--seccomp-bpf",
            "--trace=fork,clone,%file",
            "-o",
            ops::path_to_string(file)?,
            &command_string,
        ],
        EnvType::Nothing => &["-c", &command_string],
    };

    let mut child = ShellCommand::new(shell_command);
    child
        .args(arguments)
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

    if let EnvType::TraceFile(file) = &env.typ
        && let Some(parent) = file.parent()
    {
        fs::create_dir_all(parent)?;
    }

    Ok(child.spawn()?)
}

fn capture_stream<S, D>(
    config: &Config,
    source: &mut S,
    destination: &mut D,
    capture_file: &Path,
) -> Result<ChildOutput>
where
    S: Read,
    D: Write,
{
    let file = File::create(capture_file)?;
    let mut file_writer = BufWriter::with_capacity(CHUNK_SIZE, file);
    let mut chunk = [0; CHUNK_SIZE];
    let mut destination_broken = false;
    let mut length = 0;

    loop {
        let count = match source.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };

        if !destination_broken && let Err(error) = destination.write_all(&chunk[..count]) {
            if error.kind() != ErrorKind::BrokenPipe {
                return Err(error.into());
            }
            destination_broken = true;
            if !config.complete_execution {
                file_writer.write_all(&chunk[..count])?;
                file_writer.flush()?;
                return Ok(ChildOutput::BrokenPipe);
            }
        }

        file_writer.write_all(&chunk[..count])?;
        length += count;
    }

    if !destination_broken {
        destination.flush()?;
    }
    file_writer.flush()?;

    Ok(ChildOutput::Completed(length))
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
