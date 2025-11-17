use anyhow::Result;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::PathBuf;

use crate::command::Command;
use crate::config::{BUFFER_SIZE, Config, DEBUG, DEBUG_FILE};

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
        if self.directory.is_dir() {
            return Ok(());
        }
        if self.directory.is_file() {
            fs::remove_file(&self.directory)?;
        }

        fs::create_dir_all(&self.directory)?;
        if DEBUG {
            let file = File::create(self.directory.join(DEBUG_FILE))?;
            let mut file_writer = BufWriter::with_capacity(BUFFER_SIZE, file);
            serde_json::to_writer_pretty(&mut file_writer, &self.debug_info)?;
            file_writer.flush()?;
        }

        Ok(())
    }
}

#[derive(Clone, Debug, Serialize)]
struct CacheInfo {
    name: String,
    arguments: Vec<String>,
    environment: BTreeMap<String, String>,
}
