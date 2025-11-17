use anyhow::{Result, anyhow};
use fastcdc::v2020::StreamCDC;
use std::io::{self, Read};
use std::marker::PhantomData;
use std::mem;
use std::os::unix::process::CommandExt;
use std::process::Command as ShellCommand;
use std::sync::mpsc::{Receiver, Sender, SyncSender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

use crate::command::Command;
use crate::config::{CHUNK_SIZES, CHUNK_WORKERS, Config};
use crate::ops::{ExitCode, debug_log};

struct LineReader<R>
where
    R: Read,
{
    stream: R,
    stream_closed: bool,
    data: Vec<u8>,
}

impl<R> LineReader<R>
where
    R: Read,
{
    fn new(stream: R) -> Self {
        Self {
            stream,
            stream_closed: false,
            data: Vec::new(),
        }
    }
}

pub(crate) fn run(config: &Config, command: &Command) -> Result<ExitCode> {
    todo!()
}
