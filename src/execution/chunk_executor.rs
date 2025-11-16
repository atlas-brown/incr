use anyhow::Result;
use fastcdc::v2020::StreamCDC;
use std::io::{self, Read};
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;

use crate::command::Command;
use crate::config::{CHUNK_SIZES, CHUNK_WORKERS, Config};
use crate::ops::{ExitCode, debug_log};

struct LineChunker<R>
where
    R: Read,
{
    chunker: StreamCDC<R>,
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
            prefix: Vec::new(),
        }
    }
}

impl<R> Iterator for LineChunker<R>
where
    R: Read,
{
    type Item = Result<Chunk>;

    fn next(&mut self) -> Option<Result<Chunk>> {
        loop {
            let mut data = match self.chunker.next() {
                Some(Ok(chunk)) => chunk.data,
                Some(Err(error)) => return Some(Err(error.into())),
                None => {
                    if !self.prefix.is_empty() {
                        self.prefix.push(b'\n');
                        return Some(Ok(Chunk {
                            prefix: Vec::new(),
                            data: mem::take(&mut self.prefix),
                        }));
                    } else {
                        return None;
                    }
                }
            };

            match data.iter().rposition(|&b| b == b'\n') {
                Some(index) => {
                    let next_prefix = data.split_off(index + 1);
                    let prefix = mem::take(&mut self.prefix);
                    self.prefix = next_prefix;
                    return Some(Ok(Chunk { prefix, data }));
                }
                None => self.prefix.extend_from_slice(&data),
            }
        }
    }
}

#[derive(Clone, Debug)]
struct Chunk {
    prefix: Vec<u8>,
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
