use anyhow::{Result, anyhow};
use bincode::Encode;
use std::collections::{BTreeMap, HashSet};
use std::env;
use std::fs;
use std::io::{self, Error as IoError, ErrorKind, Read, Write};
use std::mem;
use std::os::unix::process::CommandExt;
use std::path::Path;
use std::process::{Child, Command as ShellCommand, Stdio};
use std::thread::{self, JoinHandle};

use crate::config::{CHUNK_SIZE, Config, EXCLUDED_VARIABLES, STRACE_COMMAND, TRACE_FILE, TRY_COMMAND};
use crate::ops;

#[derive(Clone, Debug, Encode)]
pub(crate) struct Command {
    pub(crate) name: String,
    pub(crate) arguments: Vec<String>,
    pub(crate) environment: BTreeMap<String, String>,
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

pub(crate) fn get_command() -> Result<Option<Command>> {
    let mut arguments = env::args().collect::<Vec<String>>();
    if arguments.len() <= 1 {
        return Ok(None);
    }

    if arguments.len() == 2 {
        let command_string = mem::take(&mut arguments[1]);
        arguments = shlex::split(&command_string).ok_or(anyhow!("Could not split command"))?
    } else {
        arguments.remove(0);
    };
    let name = arguments.remove(0);

    let excluded_vars = EXCLUDED_VARIABLES.iter().copied().collect::<HashSet<_>>();
    let mut environment = BTreeMap::new();
    for (var, value) in env::vars() {
        if !excluded_vars.contains(var.as_str()) {
            environment.insert(var, value);
        }
    }

    Ok(Some(Command {
        name,
        arguments,
        environment,
    }))
}

pub(crate) fn spawn_command(
    config: &Config,
    command: &Command,
    sandbox_directory: &Path,
) -> Result<ChildContext> {
    fs::create_dir_all(sandbox_directory)?;
    let mut child = spawn_child(command, sandbox_directory)?;

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

fn spawn_child(command: &Command, sandbox_directory: &Path) -> Result<Child> {
    let mut command_parts = Vec::with_capacity(command.arguments.len() + 1);
    command_parts.push(command.name.as_str());
    command_parts.extend(command.arguments.iter().map(|a| a.as_str()));
    let command_string = shlex::try_join(command_parts)?;

    let arguments = &[
        "-D",
        ops::path_to_string(sandbox_directory)?,
        STRACE_COMMAND,
        "-yf",
        "--seccomp-bpf",
        "--trace=fork,clone,%file",
        "-o",
        &format!("/tmp/{TRACE_FILE}"),
        "bash",
        "-c",
        &shlex::try_quote(&command_string)?,
    ];

    let mut child = ShellCommand::new(TRY_COMMAND);
    child
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    unsafe {
        child.pre_exec(|| {
            if libc::setsid() == -1 {
                Err(IoError::last_os_error())
            } else {
                Ok(())
            }
        });
    }

    child.spawn().map_err(|e| e.into())
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
                if !config.complete_after_downstream_failure {
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
