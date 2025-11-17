use anyhow::Result;
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::PathBuf;

use crate::cache;
use crate::command::Command;
use crate::config::{Config, DEBUG};

#[derive(Clone, Debug)]
pub(crate) struct CacheCursor {
    directory: PathBuf,
    try_command: String,
    debug_info: Option<CacheInfo>,
}

impl CacheCursor {
    pub(crate) fn new(config: &Config, command: &Command) -> Result<Self> {
        let debug_info = if DEBUG {
            Some(CacheInfo {
                name: command.name.clone(),
                arguments: command.arguments.clone(),
                environment: command.environment.clone(),
            })
        } else {
            None
        };
        Ok(Self {
            directory: config.cache_directory.join(format!("chunk_{}", command.hash)),
            try_command: config.try_command.clone(),
            debug_info,
        })
    }

    pub(crate) fn create_directory(&self) -> Result<()> {
        cache::create_directory(&self.directory, self.debug_info.as_ref())
    }
}

#[derive(Clone, Debug, Serialize)]
struct CacheInfo {
    name: String,
    arguments: Vec<String>,
    environment: BTreeMap<String, String>,
}
