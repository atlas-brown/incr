use anyhow::{Result, anyhow};
use fastcdc::v2020::{
    self as cdc, AVERAGE_MAX, AVERAGE_MIN, MASKS, MAXIMUM_MAX, MAXIMUM_MIN, MINIMUM_MAX, MINIMUM_MIN,
    Normalization,
};
use std::io::{self, ErrorKind, Read};
use std::marker::PhantomData;
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;
use std::sync::mpsc::{Receiver, Sender, SyncSender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

use crate::command::Command;
use crate::config::{BUFFER_SIZE, CHUNK_GRANULARITY, CHUNK_SIZES, CHUNK_WORKERS, ChunkSizes, Config};
use crate::ops::{ExitCode, debug_log};

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

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let mut line_reader = LineReader::new(io::stdin().lock(), CHUNK_GRANULARITY);
    let mut line_chunker = LineChunker::new(CHUNK_SIZES);

    let mut stdin_closed = false;
    while !stdin_closed {
        stdin_closed = line_reader.read()?;
        while let Some(lines) = line_reader.next_lines() {
            eprintln!("lines: {:?}", String::from_utf8(lines.to_vec()).unwrap());
            if line_chunker.update(lines) {
                eprintln!("--- CHUNK ---");
            }
        }
        line_reader.drain();
    }

    todo!()
}
