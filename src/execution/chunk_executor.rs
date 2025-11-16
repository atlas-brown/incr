#![allow(warnings)]
#![allow(clippy::all)]

use anyhow::{Result, anyhow};
use fastcdc::v2020::StreamCDC;
use std::io::{self, Read};
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;
use std::sync::mpsc::{Receiver, Sender, SyncSender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

use crate::command::Command;
use crate::config::{CHUNK_SIZES, CHUNK_WORKERS, Config};
use crate::ops::{ExitCode, debug_log};

struct LineChunker<R>
where
    R: Read,
{
    chunker: StreamCDC<R>,
    index: usize,
    prefix: Vec<u8>,
}

impl<R> LineChunker<R>
where
    R: Read,
{
    fn new(stream: R) -> Self {
        Self {
            chunker: StreamCDC::new(
                stream,
                CHUNK_SIZES.minimum,
                CHUNK_SIZES.average,
                CHUNK_SIZES.maximum,
            ),
            index: 0,
            prefix: Vec::new(),
        }
    }
}

impl<R> Iterator for LineChunker<R>
where
    R: Read,
{
    type Item = Result<InputChunk>;

    fn next(&mut self) -> Option<Result<InputChunk>> {
        loop {
            let mut data = match self.chunker.next() {
                Some(Ok(chunk)) => chunk.data,
                Some(Err(error)) => return Some(Err(error.into())),
                None => {
                    if self.prefix.is_empty() {
                        return None;
                    }
                    return Some(Ok(InputChunk {
                        index: self.index,
                        prefix: Vec::new(),
                        data: mem::take(&mut self.prefix),
                    }));
                }
            };

            let split_index = match data.iter().rposition(|&b| b == b'\n') {
                Some(index) => index,
                None => {
                    self.prefix.extend_from_slice(&data);
                    continue;
                }
            };

            let chunk_index = self.index;
            self.index += 1;
            let next_prefix = data.split_off(split_index + 1);
            let prefix = mem::take(&mut self.prefix);
            self.prefix = next_prefix;

            return Some(Ok(InputChunk {
                index: chunk_index,
                prefix,
                data,
            }));
        }
    }
}

#[derive(Clone, Debug)]
struct InputChunk {
    index: usize,
    prefix: Vec<u8>,
    data: Vec<u8>,
}

struct WorkerPool {
    threads: Vec<JoinHandle<Result<()>>>,
    send_channel: Option<SyncSender<InputChunk>>,
    receive_channel: Receiver<OutputChunk>,
}

impl WorkerPool {}

#[derive(Clone, Debug)]
struct OutputChunk {
    index: usize,
    data: Vec<u8>,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    let chunker = LineChunker::new(io::stdin().lock());
    for chunk in chunker {
        let chunk = chunk?;
        eprintln!(
            "{:?}{:?}",
            String::from_utf8(chunk.prefix),
            String::from_utf8(chunk.data)
        );
    }
    todo!()
}

fn process_chunks(command: &Command, channel: &Mutex<Receiver<InputChunk>>) -> Result<()> {
    loop {
        let channel = channel.lock().map_err(|e| anyhow!("{e:?}"))?;
    }
    Ok(())
}
