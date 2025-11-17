use anyhow::Result;
use bytes::{Buf, BufMut, Bytes, BytesMut};
use fastcdc::v2020::{
    self as cdc, AVERAGE_MAX, AVERAGE_MIN, MASKS, MAXIMUM_MAX, MAXIMUM_MIN, MINIMUM_MAX, MINIMUM_MIN,
    Normalization,
};
use rand::Rng;
use std::collections::VecDeque;
use std::io::{self, ErrorKind, Read};
use std::marker::PhantomData;
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::{ChildStdin, Command as ShellCommand};
use std::sync::Arc;
use std::sync::mpsc::{self, Receiver, SyncSender};
use std::thread::{self, JoinHandle};

use crate::cache::chunk_cache::CacheCursor;
use crate::command::{self, ChildContext, ChildOutput, Command, Runtime, RuntimeType};
use crate::config::{
    BUFFER_SIZE, CHUNK_GRANULARITY, CHUNK_SIZES, CHUNK_WORKERS, ChunkSizes, Config, TraceType,
};
use crate::ops::threads::{SignalReceiver, SignalSender};
use crate::ops::{self, ExitCode, debug_log};

#[derive(Clone, Debug)]
struct LineReader<R>
where
    R: Read,
{
    stream: R,
    group_size: usize,
    stream_closed: bool,

    chunk: Box<[u8; BUFFER_SIZE]>,
    data: Vec<u8>,
    start_index: usize,
    current_index: usize,
    current_lines: usize,
}

impl<R> LineReader<R>
where
    R: Read,
{
    fn new(stream: R, group_size: usize) -> Self {
        assert!(group_size > 0);
        Self {
            stream,
            group_size,
            stream_closed: false,

            chunk: vec![0; BUFFER_SIZE].into_boxed_slice().try_into().unwrap(),
            data: Vec::new(),
            start_index: 0,
            current_index: 0,
            current_lines: 0,
        }
    }

    fn read(&mut self) -> Result<bool> {
        if self.stream_closed {
            return Ok(true);
        }
        let count = loop {
            match self.stream.read(self.chunk.as_mut_slice()) {
                Ok(0) => {
                    self.stream_closed = true;
                    return Ok(true);
                }
                Ok(count) => break count,
                Err(error) if error.kind() == ErrorKind::Interrupted => continue,
                Err(error) => return Err(error.into()),
            }
        };
        self.data.extend_from_slice(&self.chunk[..count]);
        Ok(false)
    }

    fn next_lines(&mut self) -> Option<&[u8]> {
        debug_assert!(self.start_index <= self.current_index);
        debug_assert!(self.current_lines < self.group_size);

        while self.current_index < self.data.len() && self.current_lines < self.group_size {
            if self.data[self.current_index] == b'\n' {
                self.current_lines += 1;
            }
            self.current_index += 1;
        }

        if self.current_lines == self.group_size || (self.stream_closed && self.start_index < self.data.len())
        {
            let lines = &self.data[self.start_index..self.current_index];
            self.start_index = self.current_index;
            self.current_lines = 0;
            Some(lines)
        } else {
            None
        }
    }

    fn drain(&mut self) {
        self.data.drain(..self.start_index);
        self.current_index -= self.start_index;
        self.start_index = 0;
    }
}

#[derive(Clone, Debug)]
struct LineChunker {
    sizes: ChunkSizes,
    mask_s: u64,
    mask_l: u64,
    mask_s_ls: u64,
    mask_l_ls: u64,
    data: Vec<u8>,
}

impl LineChunker {
    fn new(sizes: ChunkSizes) -> Self {
        assert!(MINIMUM_MIN as usize <= sizes.minimum && sizes.minimum <= MINIMUM_MAX as usize);
        assert!(AVERAGE_MIN as usize <= sizes.average && sizes.average <= AVERAGE_MAX as usize);
        assert!(MAXIMUM_MIN as usize <= sizes.maximum && sizes.maximum <= MAXIMUM_MAX as usize);

        let average = (sizes.average as f64).log2().round() as u32;
        let normalization = Normalization::Level1.bits();
        let mask_s = MASKS[(average + normalization) as usize];
        let mask_l = MASKS[(average - normalization) as usize];

        Self {
            sizes,
            mask_s,
            mask_l,
            mask_s_ls: mask_s << 1,
            mask_l_ls: mask_l << 1,
            data: Vec::new(),
        }
    }

    fn update(&mut self, lines: &[u8]) -> bool {
        self.data.extend_from_slice(lines);
        let (_, count) = cdc::cut(
            &self.data,
            self.sizes.minimum,
            self.sizes.average,
            self.sizes.maximum,
            self.mask_s,
            self.mask_l,
            self.mask_s_ls,
            self.mask_l_ls,
        );
        if 0 < count && count < self.data.len() {
            self.data.drain(..count);
            true
        } else {
            false
        }
    }
}

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
            ops::threads::join(worker_thread)??;
        }
        let (send_channel, receive_channel) = mpsc::sync_channel(self.channel_capacity);
        let (send_signal, receive_signal) = ops::threads::create_signal();

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
            ops::threads::join(worker_thread)??;
        }
        Ok(())
    }
}

#[derive(Debug)]
struct StdinContext {
    hash: u64,
    thread: Option<JoinHandle<Result<()>>>,
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

    todo!()
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
    } = command::spawn_command(config, command, &runtime)?;

    let stdin_context = forward_stdin(stdin_channel, child.stdin.take().unwrap())?;
    eprintln!("got stdin hash: {:?}", stdin_context.hash);

    /*let mut test = Vec::new();
    for lines in stdin_channel {
        test.push(lines);
    }
    if let Some(signal) = receive_signal {
        signal.wait_until_active();
    }
    for lines in test {
        eprintln!("worker: {lines:?}");
    }
    eprintln!("worker done");
    send_signal.set_active();*/

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

fn forward_stdin(channel: Receiver<Bytes>, mut child_stdin: ChildStdin) -> Result<StdinContext> {
    todo!()
}
