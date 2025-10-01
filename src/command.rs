use anyhow::{Result, anyhow};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::io::{Read, Write};
use std::mem;
use std::path::Path;
use std::process::{Child, Command as ShellCommand, Stdio};

use crate::config::{CHUNK_SIZE, STRACE_COMMAND, TRACE_FILE, TRY_COMMAND};

#[derive(Debug)]
pub struct Command {
    pub name: String,
    pub arguments: Vec<String>,
    pub environment: BTreeMap<String, String>,
}

pub fn get_command() -> Result<Option<Command>> {
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

    Ok(Some(Command {
        name,
        arguments,
        environment: BTreeMap::new(), //env::vars().collect(),
    }))
}

pub fn spawn_command(command: &Command, sandbox_directory: &Path) -> Result<Child> {
    let mut command_parts = Vec::with_capacity(command.arguments.len() + 1);
    command_parts.push(command.name.as_str());
    command_parts.extend(command.arguments.iter().map(|a| a.as_str()));
    let command_string = shlex::try_join(command_parts)?;

    let arguments = &[
        "-D",
        sandbox_directory
            .to_str()
            .ok_or(anyhow!("Could not format sandbox directory"))?,
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

    fs::create_dir_all(&sandbox_directory)?;
    ShellCommand::new(TRY_COMMAND)
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.into())
}

pub fn capture_stream<S, D>(mut source: S, mut destination: D) -> Result<Vec<u8>>
where
    S: Read,
    D: Write,
{
    let mut data = Vec::new();
    let mut chunk = [0; CHUNK_SIZE];
    loop {
        let count = source.read(&mut chunk)?;
        if count == 0 {
            break;
        }
        destination.write_all(&chunk[..count])?;
        destination.flush()?;
        data.extend_from_slice(&chunk[..count]);
    }
    Ok(data)
}
