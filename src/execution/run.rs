use anyhow::Result;
use std::fs::File;
use std::io::{self, BufReader, ErrorKind, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::thread::JoinHandle;
use zstd::Decoder;

use crate::cache::{CacheData, StdoutFileState, batch_cache};
use crate::command::{ChildResult, Runtime, RuntimeType};
use crate::config::{BUFFER_SIZE, Config};
use crate::ops::stream::TransferOutcome;
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode};

#[derive(Clone, Debug, Default)]
pub(crate) struct OutputMetadata {
    pub(crate) stdout_length: usize,
    pub(crate) stderr_length: usize,
    pub(crate) broken_pipe: bool,
}

/// Joins the stdin/stdout/stderr capture threads and returns output lengths.
/// Returns `None` when short-circuiting stopped capture before completion.
pub(crate) fn join_stream_threads(
    stdin_thread: Option<JoinHandle<Result<TransferOutcome>>>,
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
    // Drop the Observe debug temp file if the flush path did not already.
    if let Some(observe_debug) = runtime.observe_debug_file() {
        ops::file::remove_file(&observe_debug)?;
    }
    Ok(())
}

pub(crate) fn replay(
    config: &Config,
    cache: &batch_cache::CacheCursor<'_>,
    data: &CacheData,
    forwarded: &OutputMetadata,
) -> Result<ExitCode> {
    // Forwarded bytes already changed the file: don't restore.
    let stdout_before = if forwarded.stdout_length == 0 {
        stdout_file_stat()
    } else {
        None
    };
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
    if stdout == TransferOutcome::Completed
        && let (Some(recorded), Some(before)) = (data.stdout_file, stdout_before)
    {
        restore_stdout_mtime(&recorded, before);
    }
    let broken_pipe = forwarded.broken_pipe
        || stdout == TransferOutcome::BrokenPipe
        || stderr == TransferOutcome::BrokenPipe;
    if (!broken_pipe || !config.short_circuit) && !data.write_outputs.is_empty() {
        cache.commit_output()?;
    }
    Ok(if broken_pipe {
        BROKEN_PIPE_CODE
    } else {
        ExitCode(data.exit_code)
    })
}

/// Size and mtime of stdout when it is a regular file (a shell redirect).
pub(crate) fn stdout_file_stat() -> Option<(u64, (i64, i64))> {
    let mut stat: libc::stat = unsafe { std::mem::zeroed() };
    if unsafe { libc::fstat(libc::STDOUT_FILENO, &mut stat) } != 0
        || stat.st_mode & libc::S_IFMT != libc::S_IFREG
    {
        return None;
    }
    Some((stat.st_size as u64, (stat.st_mtime, stat.st_mtime_nsec)))
}

/// Kept only when the command alone appended its stdout to the file.
pub(crate) fn stdout_file_state(
    before: Option<(u64, (i64, i64))>,
    stdout_length: usize,
) -> Option<StdoutFileState> {
    let (pre_size, pre_modified) = before?;
    let (post_size, post_modified) = stdout_file_stat()?;
    (post_size == pre_size + stdout_length as u64).then_some(StdoutFileState {
        pre_size,
        pre_modified,
        post_size,
        post_modified,
    })
}

/// Restore a redirected stdout file's mtime if it was in the recorded state.
fn restore_stdout_mtime(recorded: &StdoutFileState, (pre_size, pre_modified): (u64, (i64, i64))) {
    let same_before = pre_size == recorded.pre_size
        && (pre_modified == recorded.pre_modified
            || (recorded.pre_size == 0 && recorded.post_size > 0));
    if !same_before || stdout_file_stat().map(|(size, _)| size) != Some(recorded.post_size) {
        return;
    }
    let times = [
        libc::timespec {
            tv_sec: 0,
            tv_nsec: libc::UTIME_OMIT,
        },
        libc::timespec {
            tv_sec: recorded.post_modified.0,
            tv_nsec: recorded.post_modified.1 as _,
        },
    ];
    unsafe { libc::futimens(libc::STDOUT_FILENO, times.as_ptr()) };
}

/// Replays captured data from a file to a destination stream, skipping the first
/// `start_index` bytes (which were already forwarded during speculative execution).
/// Handles both compressed and uncompressed files.
pub(crate) fn output_data<D>(
    data_file: &Path,
    start_index: usize,
    compressed: bool,
    destination: &mut D,
) -> Result<TransferOutcome>
where
    D: Write,
{
    let mut file = File::open(data_file)?;
    if !compressed {
        let length = file.metadata()?.len() as usize;
        anyhow::ensure!(start_index <= length, "speculative output exceeds cached output");
        if start_index == length {
            return Ok(TransferOutcome::Completed);
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

fn output_from_stream<S, D>(source: &mut S, destination: &mut D) -> Result<TransferOutcome>
where
    S: Read,
    D: Write,
{
    match io::copy(source, destination).and_then(|_| destination.flush()) {
        Ok(()) => Ok(TransferOutcome::Completed),
        Err(error) if error.kind() == ErrorKind::BrokenPipe => Ok(TransferOutcome::BrokenPipe),
        Err(error) => Err(error.into()),
    }
}
