use anyhow::Result;
use std::fs::File;
use std::io::{self, BufReader, ErrorKind, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::thread::JoinHandle;
use zstd::Decoder;

use crate::cache::batch_cache;
use crate::command::{ChildOutput, Runtime, RuntimeType};
use crate::config::BUFFER_SIZE;
use crate::ops;

#[derive(Clone, Debug)]
pub(crate) struct OutputMetadata {
    pub(crate) stdout_length: usize,
    pub(crate) stderr_length: usize,
}

pub(crate) fn join_stream_threads(
    stdin_thread: Option<JoinHandle<Result<()>>>,
    stdout_thread: JoinHandle<Result<ChildOutput>>,
    stderr_thread: JoinHandle<Result<ChildOutput>>,
) -> Result<Option<OutputMetadata>> {
    if let Some(stdin_thread) = stdin_thread {
        ops::thread::join(stdin_thread)??;
    }
    let stdout_result = ops::thread::join(stdout_thread)??;
    let stderr_result = ops::thread::join(stderr_thread)??;
    match (stdout_result, stderr_result) {
        (ChildOutput::Completed(stdout_length), ChildOutput::Completed(stderr_length)) => {
            Ok(Some(OutputMetadata {
                stdout_length,
                stderr_length,
            }))
        }
        (ChildOutput::BrokenPipe, _) | (_, ChildOutput::BrokenPipe) => Ok(None),
    }
}

pub(crate) fn clean_child_runtime(runtime: &Runtime) -> Result<()> {
    ops::file::remove_file(&runtime.stdout_file)?;
    ops::file::remove_file(&runtime.stderr_file)?;
    match &runtime.typ {
        RuntimeType::Sandbox(directory) => batch_cache::remove_sandbox(directory)?,
        RuntimeType::TraceFile(file) => ops::file::remove_file(file)?,
        RuntimeType::Nothing => (),
    }
    Ok(())
}

pub(crate) fn output_data<D>(
    data_file: &Path,
    start_index: usize,
    destination: &mut D,
    compressed: bool,
) -> Result<bool>
where
    D: Write,
{
    let mut file = File::open(data_file)?;
    if !compressed {
        let length = file.metadata()?.len() as usize;
        assert!(start_index <= length);
        if start_index == length {
            return Ok(true);
        }
    }

    if !compressed {
        file.seek(SeekFrom::Start(start_index as u64))?;
        let mut file_reader = BufReader::with_capacity(BUFFER_SIZE, file);
        output_from_stream(&mut file_reader, destination)
    } else {
        let mut decompressor = Decoder::new(BufReader::with_capacity(BUFFER_SIZE, file))?;
        io::copy(&mut (&mut decompressor).take(start_index as u64), &mut io::sink())?;
        output_from_stream(&mut decompressor, destination)
    }
}

fn output_from_stream<S, D>(source: &mut S, destination: &mut D) -> Result<bool>
where
    S: Read,
    D: Write,
{
    match io::copy(source, destination) {
        Ok(_) => {
            destination.flush()?;
            Ok(true)
        }
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(false),
        Err(error) => Err(error.into()),
    }
}
