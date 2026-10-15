use anyhow::Result;
use bincode::{Decode, Encode};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use crate::config::{BUFFER_SIZE, DEBUG_FILE};

pub(crate) mod batch_cache;
pub(crate) mod candidates;
pub(crate) mod effects;

#[derive(Clone, Debug, Decode, Deserialize, Encode, Serialize)]
pub(crate) struct CacheData {
    pub(crate) exit_code: i32,
    pub(crate) replay_barriers: Vec<String>,
    pub(crate) read_dependencies: HashMap<PathBuf, DependencyKey>,
    pub(crate) write_outputs: HashSet<PathBuf>,
    pub(crate) compressed_output: bool,
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Eq, PartialEq, Serialize)]
pub(crate) enum DependencyKey {
    DoesNotExist,
    ParentDirectory {
        mode: u32,
        uid: u32,
        gid: u32,
        access: u8,
    },
    Uncacheable,
    All(Vec<DependencyKey>),
    FileState {
        modified: u128,
        changed_sec: i64,
        changed_nsec: i64,
        size: u64,
        mode: u32,
    },
    DirectoryState {
        modified: u128,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
    },
    SymlinkState {
        target: PathBuf,
        modified: u128,
        changed_sec: i64,
        changed_nsec: i64,
        mode: u32,
    },
    Hash(u64),
    /// An observed full overwrite may start from its original precondition or
    /// its own exact completed file. It may not consume arbitrary changed bytes.
    Overwrite {
        initial: Box<DependencyKey>,
        output: ProducedFile,
    },
    /// Lookup failed because an intermediate component was not a directory.
    NotDirectory,
    /// Read-only workspace data: identity and ctime are witnesses, not outputs.
    /// Modification time, content and access metadata remain dependencies.
    FileContent {
        modified: u128,
        changed_sec: i64,
        changed_nsec: i64,
        file: ProducedFile,
    },
}

#[derive(Clone, Debug, Decode, Deserialize, Encode, Eq, PartialEq, Serialize)]
pub(crate) struct ProducedFile {
    pub(crate) device: u64,
    pub(crate) inode: u64,
    pub(crate) size: u64,
    pub(crate) mode: u32,
    pub(crate) uid: u32,
    pub(crate) gid: u32,
    pub(crate) links: u64,
    pub(crate) access: u8,
    pub(crate) hash: u64,
}

impl CacheData {
    /// Cache-format limitations belong here, not in the trace's effect barriers:
    /// a losslessly traced byte path can still be restored after speculation.
    pub(crate) fn is_reusable(&self) -> bool {
        self.replay_barriers.is_empty()
            && self
                .read_dependencies
                .iter()
                .all(|(path, dependency)| path.to_str().is_some() && dependency.is_reusable())
            && self.write_outputs.iter().all(|path| path.to_str().is_some())
    }
}

impl DependencyKey {
    fn is_reusable(&self) -> bool {
        match self {
            Self::Uncacheable => false,
            Self::SymlinkState { target, .. } => target.to_str().is_some(),
            Self::All(dependencies) => dependencies.iter().all(Self::is_reusable),
            Self::Overwrite { initial, .. } => initial.is_reusable(),
            _ => true,
        }
    }
}

pub(crate) fn create_directory<D>(directory: &Path, debug_info: Option<&D>) -> Result<()>
where
    D: Serialize,
{
    if directory.is_dir() {
        return Ok(());
    }
    if directory.is_file() {
        fs::remove_file(directory)?;
    }

    fs::create_dir_all(directory)?;
    if let Some(debug_info) = debug_info {
        let file = File::create(directory.join(DEBUG_FILE))?;
        let mut file_writer = BufWriter::with_capacity(BUFFER_SIZE, file);
        serde_json::to_writer_pretty(&mut file_writer, debug_info)?;
        file_writer.flush()?;
    }

    Ok(())
}
