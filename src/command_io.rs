use anyhow::{Result, anyhow};
use std::collections::HashMap;
use std::env;
use std::mem;

#[derive(Debug)]
pub struct Command {
    pub name: String,
    pub arguments: Vec<String>,
    pub environment: HashMap<String, String>,
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
        environment: HashMap::new(), //env::vars().collect(),
    }))
}
