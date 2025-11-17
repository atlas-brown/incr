use anyhow::{Result, anyhow};
use fastcdc::v2020::StreamCDC;
use std::io::{self, ErrorKind, Read};
use std::marker::PhantomData;
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;
use std::sync::mpsc::{Receiver, Sender, SyncSender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

use crate::command::Command;
use crate::config::{BUFFER_SIZE, CHUNK_SIZES, CHUNK_WORKERS, Config};
use crate::ops::{ExitCode, debug_log};

struct LineReader<R>
where
    R: Read,
{
    stream: R,
    stream_closed: bool,
    chunk: Box<[u8; BUFFER_SIZE]>,
    data: Vec<u8>,
    index: usize,
}

impl<R> LineReader<R>
where
    R: Read,
{
    fn new(stream: R) -> Self {
        Self {
            stream,
            stream_closed: false,
            chunk: vec![0; BUFFER_SIZE].into_boxed_slice().try_into().unwrap(),
            data: Vec::new(),
            index: 0,
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

    fn next_line(&mut self) -> Option<&[u8]> {
        let mut end_index = self.index;
        while end_index < self.data.len() && self.data[end_index] != b'\n' {
            end_index += 1;
        }
        if end_index < self.data.len() {
            let line = &self.data[self.index..end_index + 1];
            self.index = end_index + 1;
            Some(line)
        } else if self.stream_closed && self.index < self.data.len() {
            let line = &self.data[self.index..];
            self.index = self.data.len();
            Some(line)
        } else {
            None
        }
    }

    fn drain(&mut self) {
        self.data.drain(..self.index);
        self.index = 0;
    }
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let mut line_reader = LineReader::new(io::stdin().lock());
    let mut stdin_closed = false;
    while !stdin_closed {
        stdin_closed = line_reader.read()?;
        while let Some(line) = line_reader.next_line() {
            eprintln!("line: {:?}", String::from_utf8(line.to_vec()).unwrap());
        }
        line_reader.drain();
    }
    todo!()
}
