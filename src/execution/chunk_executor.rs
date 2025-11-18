use anyhow::Result;
use bytes::{Bytes, BytesMut};
use rand::Rng;
use std::collections::VecDeque;
use std::io::{self, ErrorKind, Read, Write};
use std::marker::PhantomData;
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::{ChildStdin, Command as ShellCommand};
use std::sync::Arc;
use std::sync::mpsc::{self, Receiver, SyncSender};
use std::thread::{self, JoinHandle};
use xxhash_rust::xxh3::Xxh3;

use crate::cache::chunk_cache::CacheCursor;
use crate::command::{self, ChildContext, ChildOutput, Command, Runtime, RuntimeType};
use crate::config::{CHUNK_GRANULARITY, CHUNK_SIZES, CHUNK_WORKERS, Config, TraceType};
use crate::ops::chunk::{LineChunker, LineReader};
use crate::ops::thread::{SignalReceiver, SignalSender};
use crate::ops::{self, ExitCode, debug_log};

#[derive(Debug)]
struct WorkerPool {
    config: Config,
    command: Arc<Command>,
    cache: Arc<CacheCursor>,
    max_workers: usize,
    channel_capacity: usize,

    processing: VecDeque<JoinHandle<Result<()>>>,
    current_thread: Option<JoinHandle<Result<()>>>,
    current_channel: Option<SyncSender<Bytes>>,
    next_signal: Option<SignalReceiver>,
    data: BytesMut,
}

impl WorkerPool {
    fn new(
        config: Config,
        command: Command,
        cache: CacheCursor,
        max_workers: usize,
        channel_capacity: usize,
    ) -> Self {
        assert!(max_workers > 0 && channel_capacity > 0);
        Self {
            config,
            command: Arc::new(command),
            cache: Arc::new(cache),
            max_workers,
            channel_capacity,

            processing: VecDeque::with_capacity(max_workers),
            current_thread: None,
            current_channel: None,
            next_signal: None,
            data: BytesMut::new(),
        }
    }

    fn send_lines(&mut self, lines: &[u8]) -> Result<()> {
        let channel = self.current_channel.as_ref().unwrap();
        self.data.extend_from_slice(lines);
        let lines = self.data.split();
        channel.send(lines.freeze())?;
        Ok(())
    }

    fn start_worker(&mut self) -> Result<()> {
        assert!(self.current_thread.is_none() && self.current_channel.is_none());
        assert!(self.processing.len() <= self.max_workers);

        if self.processing.len() == self.max_workers {
            let worker_thread = self.processing.pop_front().unwrap();
            ops::thread::join(worker_thread)??;
        }
        let (send_channel, receive_channel) = mpsc::sync_channel(self.channel_capacity);
        let (send_signal, receive_signal) = ops::thread::create_signal();

        self.current_thread = Some(thread::spawn({
            let config = self.config.clone();
            let command = Arc::clone(&self.command);
            let cache = Arc::clone(&self.cache);
            let receive_signal = self.next_signal.take();
            move || {
                process_chunk(
                    &config,
                    &command,
                    &cache,
                    receive_channel,
                    receive_signal,
                    send_signal,
                )
            }
        }));
        self.current_channel = Some(send_channel);
        self.next_signal = Some(receive_signal);

        Ok(())
    }

    fn detach_worker(&mut self) {
        assert!(self.current_thread.is_some() && self.current_channel.is_some());
        self.processing.push_back(self.current_thread.take().unwrap());
        self.current_channel.take();
    }

    fn join(self) -> Result<()> {
        assert!(self.current_thread.is_none() && self.current_channel.is_none());
        for worker_thread in self.processing {
            eprintln!("joining");
            ops::thread::join(worker_thread)??;
        }
        Ok(())
    }
}

#[derive(Debug)]
struct StdinContext {
    hash: u64,
    thread: JoinHandle<Result<()>>,
}

pub(crate) fn run(config: Config, command: Command) -> Result<ExitCode> {
    let cache = CacheCursor::new(&config, &command)?;
    cache.create_directory()?;
    let channel_capacity = CHUNK_SIZES.average / (2 * CHUNK_GRANULARITY);
    let mut worker_pool = WorkerPool::new(config, command, cache, CHUNK_WORKERS, channel_capacity);
    worker_pool.start_worker()?;

    {
        let mut stdin_reader = LineReader::new(io::stdin().lock(), CHUNK_GRANULARITY);
        let mut stdin_chunker = LineChunker::new(CHUNK_SIZES);
        let mut stdin_closed = false;

        while !stdin_closed {
            stdin_closed = stdin_reader.read()?;
            while let Some(lines) = stdin_reader.next_lines() {
                worker_pool.send_lines(lines)?;
                if stdin_chunker.update(lines) {
                    worker_pool.detach_worker();
                    worker_pool.start_worker()?;
                }
            }
            stdin_reader.drain();
        }

        worker_pool.detach_worker();
    }

    worker_pool.join()?;
    eprintln!("joined");

    Ok(ExitCode(0))
}

fn process_chunk(
    config: &Config,
    command: &Command,
    cache: &CacheCursor,
    stdin_channel: Receiver<Bytes>,
    receive_signal: Option<SignalReceiver>,
    send_signal: SignalSender,
) -> Result<()> {
    let runtime = create_child_runtime(config)?;
    let ChildContext {
        mut child,
        stdout_thread,
        stderr_thread,
    } = match receive_signal {
        Some(signal) => command::spawn_with_signal(config, command, &runtime, signal)?,
        None => command::spawn(config, command, &runtime)?,
    };

    let stdin_context = forward_stdin(stdin_channel, child.stdin.take().unwrap())?;

    ops::thread::join(stdin_context.thread)??;
    let result = child.wait()?;
    eprintln!("got stdin hash: {:?}", stdin_context.hash);
    eprintln!("result: {result:?}");
    send_signal.signal_ready();

    Ok(())
}

fn create_child_runtime(config: &Config) -> Result<Runtime> {
    assert!(config.trace_type == TraceType::Nothing);
    let key = rand::rng().random_range(0..u64::MAX);
    let stdout_file = config.cache_directory.join(format!("stdout_{key}.incr"));
    let stderr_file = config.cache_directory.join(format!("stderr_{key}.incr"));
    Ok(Runtime {
        typ: RuntimeType::Nothing,
        stdout_file,
        stderr_file,
    })
}

fn forward_stdin(stdin_channel: Receiver<Bytes>, mut child_stdin: ChildStdin) -> Result<StdinContext> {
    let channel_capacity = CHUNK_SIZES.average / (2 * CHUNK_GRANULARITY);
    let (send_channel, receive_channel) = mpsc::sync_channel::<Bytes>(channel_capacity);
    let stdin_thread = thread::spawn(move || {
        let mut broken = false;
        for lines in receive_channel {
            if broken {
                continue;
            }
            if let Err(error) = child_stdin.write_all(&lines) {
                if error.kind() != ErrorKind::BrokenPipe {
                    return Err(error.into());
                }
                broken = true;
            };
        }
        Ok(())
    });

    let mut hasher = Xxh3::new();
    for lines in stdin_channel {
        hasher.update(&lines);
        send_channel.send(lines)?;
    }

    Ok(StdinContext {
        hash: hasher.digest(),
        thread: stdin_thread,
    })
}
