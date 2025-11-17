use anyhow::Result;
use serde::{Deserialize, Serialize};

use crate::command::Command;
use crate::config::{Config, DEBUG};

#[derive(Clone, Debug)]
pub(crate) struct CacheCursor {}

impl CacheCursor {
    pub(crate) fn new(config: &Config, command: &Command) -> Result<Self> {
        Ok(Self {})
    }

    pub(crate) fn create_directory(&self) -> Result<()> {
        /*if self.directory.is_dir() {
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
        }*/

        Ok(())
    }
}
