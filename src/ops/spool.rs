//! Bounded-memory buffering for speculative input and ordered output.
use anyhow::Result;
use std::collections::VecDeque;
use std::fs::{self, File, OpenOptions};
use std::io::{ErrorKind, Write};
use std::os::unix::fs::{FileExt, OpenOptionsExt};
use std::path::Path;
use std::sync::{Arc, Condvar, Mutex};

use crate::config::BUFFER_SIZE;
use crate::execution::run::ForwardResult;

const MEMORY_LIMIT: usize = 1024 * 1024;

#[derive(Default)]
struct State {
    chunks: VecDeque<Vec<u8>>,
    buffered: usize,
    file: Option<File>,
    written: u64,
    consumed: u64,
    completed: bool,
    receiver_closed: bool,
}

#[derive(Default)]
struct Shared {
    state: Mutex<State>,
    available: Condvar,
}

pub(crate) struct Sender {
    shared: Arc<Shared>,
    directory: std::path::PathBuf,
}

pub(crate) struct Receiver(Arc<Shared>);

pub(crate) fn create(directory: &Path) -> (Sender, Receiver) {
    let shared = Arc::new(Shared::default());
    (
        Sender {
            shared: Arc::clone(&shared),
            directory: directory.to_owned(),
        },
        Receiver(shared),
    )
}

impl Sender {
    pub(crate) fn send(&self, bytes: &[u8]) -> Result<bool> {
        let mut state = self.shared.state.lock().unwrap();
        if state.receiver_closed {
            return Ok(false);
        }
        if state.file.is_none() && state.buffered + bytes.len() <= MEMORY_LIMIT {
            state.chunks.push_back(bytes.to_vec());
            state.buffered += bytes.len();
        } else {
            if state.file.is_none() {
                fs::create_dir_all(&self.directory)?;
                let path = self
                    .directory
                    .join(format!("buffer-{:032x}.tmp", rand::random::<u128>()));
                let file = OpenOptions::new()
                    .read(true)
                    .write(true)
                    .create_new(true)
                    .mode(0o600)
                    .open(&path)?;
                // Unix keeps the open file alive without a pathname to clean after cancellation.
                fs::remove_file(path)?;
                state.file = Some(file);
            }
            state.file.as_ref().unwrap().write_all_at(bytes, state.written)?;
            state.written += bytes.len() as u64;
        }
        self.shared.available.notify_one();
        Ok(true)
    }
}

impl Drop for Sender {
    fn drop(&mut self) {
        self.shared.state.lock().unwrap().completed = true;
        self.shared.available.notify_one();
    }
}

impl Receiver {
    pub(crate) fn forward(self, mut destination: impl Write) -> Result<ForwardResult> {
        let mut buffer = vec![0; BUFFER_SIZE];
        loop {
            let mut state = self.0.state.lock().unwrap();
            let (chunk, length) = loop {
                if let Some(chunk) = state.chunks.pop_front() {
                    state.buffered -= chunk.len();
                    let length = chunk.len();
                    break (Some(chunk), length);
                }
                if state.consumed < state.written {
                    let length = (state.written - state.consumed).min(buffer.len() as u64) as usize;
                    state
                        .file
                        .as_ref()
                        .unwrap()
                        .read_exact_at(&mut buffer[..length], state.consumed)?;
                    state.consumed += length as u64;
                    break (None, length);
                }
                if state.completed {
                    return Ok(ForwardResult::Completed);
                }
                state = self.0.available.wait(state).unwrap();
            };
            let bytes = match &chunk {
                Some(chunk) => chunk.as_slice(),
                None => &buffer[..length],
            };
            drop(state);
            if let Err(error) = destination.write_all(bytes) {
                return if error.kind() == ErrorKind::BrokenPipe {
                    Ok(ForwardResult::BrokenPipe)
                } else {
                    Err(error.into())
                };
            }
        }
    }
}

impl Drop for Receiver {
    fn drop(&mut self) {
        self.0.state.lock().unwrap().receiver_closed = true;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn closed_receiver_stops_producer() -> Result<()> {
        let (sender, receiver) = create(Path::new("unused-spool-directory"));
        drop(receiver);
        assert!(!sender.send(b"unused")?);
        Ok(())
    }

    #[test]
    fn spilled_input_preserves_order_and_cleans_path() -> Result<()> {
        let directory = std::env::temp_dir().join(format!("incr-spool-{}", rand::random::<u128>()));
        let (sender, receiver) = create(&directory);
        let input: Vec<u8> = (0..MEMORY_LIMIT * 3 + 137)
            .map(|index| (index % 251) as u8)
            .collect();
        for chunk in input.chunks(7777) {
            assert!(sender.send(chunk)?);
        }
        assert!(sender.shared.state.lock().unwrap().buffered <= MEMORY_LIMIT);
        assert!(sender.shared.state.lock().unwrap().file.is_some());
        assert_eq!(fs::read_dir(&directory)?.count(), 0);
        drop(sender);
        let mut output = Vec::new();
        assert_eq!(receiver.forward(&mut output)?, ForwardResult::Completed);
        fs::remove_dir(directory)?;
        assert_eq!(output, input);
        Ok(())
    }
}
