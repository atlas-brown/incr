use anyhow::Result;
use fastcdc::v2020::StreamCDC;
use std::io::Read;
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
        }
    }
}

impl<R> Iterator for LineChunker<R>
where
    R: Read,
{
    type Item = Result<Chunk>;

    fn next(&mut self) -> Option<Result<Chunk>> {
        todo!()
    }
}

struct Chunk {
    prefix: Vec<u8>,
    data: Vec<u8>,
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    todo!()
}
