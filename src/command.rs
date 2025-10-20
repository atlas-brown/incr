use anyhow::{Result, anyhow, ensure};
use bincode::Encode;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs;
use std::io::{self, Error as IoError, ErrorKind, Read, Write};
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
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
pub(crate) enum ChildEnv {
    Sandbox(PathBuf),
    TraceFile(PathBuf),
    Nothing,
}

#[derive(Debug)]
pub(crate) struct ChildContext {
    pub(crate) child: Child,
    pub(crate) stdout_thread: JoinHandle<Result<Output>>,
    pub(crate) stderr_thread: JoinHandle<Result<Output>>,
}

#[derive(Clone, Debug)]
pub(crate) enum Output {
    Completed(Vec<u8>),
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
    if let ChildEnv::Sandbox(directory) = env {
        fs::create_dir_all(directory)?;
    }
    let mut child = spawn_child(command, env)?;

    let child_stdout = child.stdout.take().unwrap();
    let child_stderr = child.stderr.take().unwrap();
    let stdout_thread = thread::spawn({
        let config = config.clone();
        move || capture_stream(&config, child_stdout, io::stdout())
    });
    let stderr_thread = thread::spawn({
        let config = config.clone();
        move || capture_stream(&config, child_stderr, io::stderr())
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

    let shell_command = match env {
        ChildEnv::Sandbox(_) => &command.try_command,
        ChildEnv::TraceFile(_) => STRACE_COMMAND,
        ChildEnv::Nothing => BASH_COMMAND,
    };
    let arguments = match env {
        ChildEnv::Sandbox(directory) => &[
            "-D",
            ops::path_to_string(directory)?,
            STRACE_COMMAND,
            "-yf",
            "--seccomp-bpf",
            "--trace=fork,clone,%file",
            "-o",
            &format!("/tmp/{TRACE_FILE}"),
            BASH_COMMAND,
            "-c",
            &shlex::try_quote(&command_string)?,
        ] as &[&str],
        ChildEnv::TraceFile(file) => &[
            "-yf",
            "--seccomp-bpf",
            "--trace=fork,clone,%file",
            "-o",
            ops::path_to_string(file)?,
            BASH_COMMAND,
            "-c",
            &command_string,
        ],
        ChildEnv::Nothing => &["-c", &command_string],
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

    if let ChildEnv::TraceFile(file) = env
        && let Some(parent) = file.parent()
    {
        fs::create_dir_all(parent)?;
    }

    Ok(child.spawn()?)
}

fn capture_stream<S, D>(config: &Config, mut source: S, mut destination: D) -> Result<Output>
where
    S: Read,
    D: Write,
{
    let mut data = Vec::new();
    let mut chunk = [0; CHUNK_SIZE];
    let mut destination_broken = false;

    loop {
        let count = match source.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => count,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };

        if !destination_broken {
            let write_result = destination
                .write_all(&chunk[..count])
                .and_then(|_| destination.flush());
            if let Err(error) = write_result {
                if error.kind() != ErrorKind::BrokenPipe {
                    return Err(error.into());
                }
                destination_broken = true;
                if !config.complete_execution {
                    data.extend_from_slice(&chunk[..count]);
                    return Ok(Output::BrokenPipe);
                }
            }
        }

        data.extend_from_slice(&chunk[..count]);
    }

    Ok(Output::Completed(data))
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
