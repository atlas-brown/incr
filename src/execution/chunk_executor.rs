use anyhow::Result;
use std::collections::VecDeque;
use std::fs;
use std::io::{self, ErrorKind, Read};
use std::process::ChildStdin;
use std::sync::Arc;
use std::sync::mpsc::{self, Receiver, SyncSender};
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::batch_cache::CacheCursor;
use crate::command::{self, ChildContext, Command, Runtime, RuntimeType};
use crate::config::{BUFFER_SIZE, CHUNK_SIZES, CHUNK_WORKERS, Config};
use crate::execution::{dependency, record, run};
use crate::ops::chunk::ContentChunker;
use crate::ops::thread::{ReadySignal, SignalReceiver, SignalSender};
use crate::ops::{self, BROKEN_PIPE_CODE, ExitCode};

type Worker = JoinHandle<Result<i32>>;

struct WorkerPool {
    config: Arc<Config>,
    command: Arc<Command>,
    workers: VecDeque<Worker>,
    input: Option<SyncSender<Vec<u8>>>,
    previous_output: Option<SignalReceiver>,
}

impl WorkerPool {
    fn start(&mut self) -> Result<i32> {
        self.input.take();
        if self.workers.len() == CHUNK_WORKERS {
            let status = ops::thread::join(self.workers.pop_front().unwrap())??;
            if status != 0 {
                return Ok(status);
            }
        }
        let (sender, receiver) = mpsc::sync_channel(2);
        let (completed, next_output) = ops::thread::create_signal();
        let previous_output = self.previous_output.take();
        let config = Arc::clone(&self.config);
        let command = Arc::clone(&self.command);
        self.workers.push_back(thread::spawn(move || {
            let _completion = CompletionSignal(completed);
            process_chunk(&config, &command, receiver, previous_output)
        }));
        self.input = Some(sender);
        self.previous_output = Some(next_output);
        Ok(0)
    }

    fn finish(&mut self) -> Result<i32> {
        self.input.take();
        let mut status = 0;
        while let Some(worker) = self.workers.pop_front() {
            let worker_status = ops::thread::join(worker)??;
            if status == 0 {
                status = worker_status;
            }
        }
        Ok(status)
    }
}

impl Drop for WorkerPool {
    fn drop(&mut self) {
        self.input.take();
        for worker in self.workers.drain(..) {
            let _ = worker.join();
        }
    }
}

struct CompletionSignal(SignalSender);
impl Drop for CompletionSignal {
    fn drop(&mut self) {
        self.0.signal_ready();
    }
}

struct TemporaryOutput(Runtime);
impl Drop for TemporaryOutput {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0.stdout_file);
        let _ = fs::remove_file(&self.0.stderr_file);
    }
}

pub(crate) fn execute(config: Config, command: Command) -> Result<ExitCode> {
    let chunk_mode =
        crate::annotation::chunk_mode(&command, config.assume_text).expect("eligible chunk command");
    let mut pool = WorkerPool {
        config: Arc::new(config),
        command: Arc::new(command),
        workers: VecDeque::new(),
        input: None,
        previous_output: None,
    };
    pool.start()?;
    let mut input = io::stdin().lock();
    let mut buffer = [0; BUFFER_SIZE];
    let mut chunker = ContentChunker::new(CHUNK_SIZES);
    let align_lines = matches!(chunk_mode, crate::annotation::ChunkMode::Lines);
    loop {
        let length = match input.read(&mut buffer) {
            Ok(0) => break,
            Ok(length) => length,
            Err(error) if error.kind() == ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        };
        let mut remaining = &buffer[..length];
        while !remaining.is_empty() {
            let boundary = chunker.next_boundary(remaining, align_lines);
            let length = boundary.unwrap_or(remaining.len());
            if pool
                .input
                .as_ref()
                .unwrap()
                .send(remaining[..length].to_vec())
                .is_err()
            {
                let status = pool.finish()?;
                return Ok(if status == 0 {
                    BROKEN_PIPE_CODE
                } else {
                    ExitCode(status)
                });
            }
            remaining = &remaining[length..];
            if boundary.is_some() {
                let status = pool.start()?;
                if status != 0 {
                    return Ok(ExitCode(status));
                }
            }
        }
    }
    Ok(ExitCode(pool.finish()?))
}

fn process_chunk(
    config: &Config,
    command: &Command,
    input: Receiver<Vec<u8>>,
    previous_output: Option<SignalReceiver>,
) -> Result<i32> {
    let identifier = rand::random::<u128>();
    let output = TemporaryOutput(Runtime {
        kind: RuntimeType::Nothing,
        stdout_file: config.cache_directory.join(format!("stdout_{identifier}.incr")),
        stderr_file: config.cache_directory.join(format!("stderr_{identifier}.incr")),
        effect_gate: None,
        snapshot_directory: None,
    });
    let runtime = &output.0;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = match &previous_output {
        Some(signal) => command::spawn_with_signal(config, command, runtime, signal)?,
        None => command::spawn(config, command, runtime)?,
    };
    let (input_hash, input_thread) =
        forward_stdin(input, child.stdin.take().unwrap(), &config.cache_directory)?;
    let cache = CacheCursor::from_hash(config, command, input_hash)?;
    let cached = cache
        .load_data()?
        .filter(|data| dependency::check_cache_valid(&cache, data).unwrap_or(false));
    let status = if cached.is_some() {
        if child.try_wait()?.is_none() {
            command::kill_child(&child)?;
        }
        child.wait()?;
        0
    } else {
        command::exit_code(child.wait()?)
    };
    let Some(outputs) = run::join_stream_threads(Some(input_thread), stdout_thread, stderr_thread)? else {
        return Ok(BROKEN_PIPE_CODE.0);
    };
    if outputs.broken_pipe {
        return Ok(BROKEN_PIPE_CODE.0);
    }
    if let Some(cached) = cached {
        if let Some(signal) = previous_output {
            signal.wait_until_ready();
        }
        return Ok(run::replay(config, &cache, &cached, &outputs)?.0);
    }
    cache.create_directory()?;
    cache.clean()?;
    let data = record::capture(config, &cache, runtime, status)?;
    cache.save_data(&data)?;
    Ok(status)
}

fn forward_stdin(
    input: Receiver<Vec<u8>>,
    child_stdin: ChildStdin,
    directory: &std::path::Path,
) -> Result<(u64, JoinHandle<Result<run::ForwardResult>>)> {
    let (sender, receiver) = ops::spool::create(directory);
    let worker = thread::spawn(|| receiver.forward(child_stdin));
    let mut hasher = Xxh3::new();
    for bytes in input {
        hasher.update(&bytes);
        if !sender.send(&bytes)? {
            break;
        }
    }
    Ok((hasher.digest(), worker))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{EffectPolicy, TraceType};

    #[test]
    fn preserves_nonzero_status_on_cold_and_cached_chunks() -> Result<()> {
        let directory = std::env::temp_dir().join(format!("incr-chunk-status-{}", rand::random::<u128>()));
        fs::create_dir(&directory)?;
        let result = (|| -> Result<()> {
            let config = Config {
                try_command: String::new(),
                cache_directory: directory.clone(),
                trace_type: TraceType::Nothing,
                observe_command: None,
                effect_policy: EffectPolicy::Live,
                assume_text: false,
                batch_executor: false,
                short_circuit: false,
                compress_output: true,
                full_tracing: false,
                enable_annotations: true,
                skip_introspection: true,
            };
            let environment =
                std::collections::HashMap::from([("PATH".to_owned(), "/usr/bin:/bin".to_owned())]);
            let command = command::create(vec!["sh".into(), "-c".into(), "exit 7".into()], &environment)?;
            for _ in 0..2 {
                let (sender, receiver) = mpsc::channel();
                drop(sender);
                anyhow::ensure!(
                    process_chunk(&config, &command, receiver, None)? == 7,
                    "lost child exit status"
                );
            }
            Ok(())
        })();
        fs::remove_dir_all(directory)?;
        result
    }
}
