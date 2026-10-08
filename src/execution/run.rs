use anyhow::Result;
use std::fs::File;
use std::io::{self, BufReader, ErrorKind, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::thread::JoinHandle;
use zstd::Decoder;

use crate::cache::{CacheData, batch_cache};
use crate::command::{ChildResult, Runtime, RuntimeType};
use crate::config::{BUFFER_SIZE, Config};
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode};

#[derive(Clone, Debug, Default)]
pub(crate) struct OutputMetadata {
    pub(crate) stdout_length: usize,
    pub(crate) stderr_length: usize,
    pub(crate) broken_pipe: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum OutputResult {
    Completed,
    BrokenPipe,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum ForwardResult {
    Completed,
    BrokenPipe,
}

/// Joins the stdin/stdout/stderr capture threads and returns output lengths.
/// Returns `None` when short-circuiting stopped capture before completion.
pub(crate) fn join_stream_threads(
    stdin_thread: Option<JoinHandle<Result<ForwardResult>>>,
    stdout_thread: JoinHandle<Result<ChildResult>>,
    stderr_thread: JoinHandle<Result<ChildResult>>,
) -> Result<Option<OutputMetadata>> {
    if let Some(stdin_thread) = stdin_thread {
        ops::thread::join(stdin_thread)??;
    }
    let stdout_result = ops::thread::join(stdout_thread)??;
    let stderr_result = ops::thread::join(stderr_thread)??;
    match (stdout_result, stderr_result) {
        (
            ChildResult::Completed {
                length: stdout_length,
                broken_pipe: stdout_broken,
            },
            ChildResult::Completed {
                length: stderr_length,
                broken_pipe: stderr_broken,
            },
        ) => Ok(Some(OutputMetadata {
            stdout_length,
            stderr_length,
            broken_pipe: stdout_broken || stderr_broken,
        })),
        (ChildResult::BrokenPipe, _) | (_, ChildResult::BrokenPipe) => Ok(None),
    }
}

pub(crate) struct TemporaryRuntime<'runtime>(pub(crate) &'runtime Runtime);

impl Drop for TemporaryRuntime<'_> {
    fn drop(&mut self) {
        let _ = clean_child_runtime(self.0);
    }
}

/// Removes temporary runtime files (stdout/stderr captures, sandbox, or trace file).
pub(crate) fn clean_child_runtime(runtime: &Runtime) -> Result<()> {
    ops::file::remove_file(&runtime.stdout_file)?;
    ops::file::remove_file(&runtime.stderr_file)?;
    if let Some(directory) = &runtime.snapshot_directory {
        ops::file::remove_directory(directory)?;
    }
    match &runtime.kind {
        RuntimeType::Sandbox(directory) => batch_cache::remove_sandbox(directory)?,
        RuntimeType::TraceFile(file) | RuntimeType::Observe(file) => ops::file::remove_file(file)?,
        RuntimeType::Nothing => (),
    }
    Ok(())
}

pub(crate) fn replay(
    config: &Config,
    cache: &batch_cache::CacheCursor<'_>,
    data: &CacheData,
    forwarded: &OutputMetadata,
) -> Result<ExitCode> {
    let stdout = output_data(
        &cache.get_stdout_file(),
        forwarded.stdout_length,
        data.compressed_output,
        &mut io::stdout().lock(),
    )?;
    let stderr = output_data(
        &cache.get_stderr_file(),
        forwarded.stderr_length,
        data.compressed_output,
        &mut io::stderr().lock(),
    )?;
    let broken_pipe =
        forwarded.broken_pipe || stdout == OutputResult::BrokenPipe || stderr == OutputResult::BrokenPipe;
    if (!broken_pipe || !config.short_circuit) && !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    Ok(if broken_pipe {
        BROKEN_PIPE_CODE
    } else {
        ExitCode(data.exit_code)
    })
}

/// Replays captured data from a file to a destination stream, skipping the first
/// `start_index` bytes (which were already forwarded during speculative execution).
/// Handles both compressed and uncompressed files.
pub(crate) fn output_data<D>(
    data_file: &Path,
    start_index: usize,
    compressed: bool,
    destination: &mut D,
) -> Result<OutputResult>
where
    D: Write,
{
    let mut file = File::open(data_file)?;
    if !compressed {
        let length = file.metadata()?.len() as usize;
        anyhow::ensure!(start_index <= length, "speculative output exceeds cached output");
        if start_index == length {
            return Ok(OutputResult::Completed);
        }
    }

    if !compressed {
        file.seek(SeekFrom::Start(start_index as u64))?;
        let mut file_reader = BufReader::with_capacity(BUFFER_SIZE, file);
        output_from_stream(&mut file_reader, destination)
    } else {
        let mut decompressor = Decoder::new(BufReader::with_capacity(BUFFER_SIZE, file))?;
        let skipped = io::copy(&mut (&mut decompressor).take(start_index as u64), &mut io::sink())?;
        anyhow::ensure!(
            skipped == start_index as u64,
            "speculative output exceeds cached output"
        );
        output_from_stream(&mut decompressor, destination)
    }
}

fn output_from_stream<S, D>(source: &mut S, destination: &mut D) -> Result<OutputResult>
where
    S: Read,
    D: Write,
{
    match io::copy(source, destination).and_then(|_| destination.flush()) {
        Ok(()) => Ok(OutputResult::Completed),
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(OutputResult::BrokenPipe),
        Err(error) => Err(error.into()),
    }
}
