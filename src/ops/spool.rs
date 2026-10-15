//! Bounded-memory buffering for speculative input and ordered output.
use anyhow::Result;
use std::collections::VecDeque;
use std::fs::{self, File, OpenOptions};
use std::io::{ErrorKind, Write};
use std::os::unix::fs::{FileExt, OpenOptionsExt};
use std::path::Path;
use std::sync::{Arc, Condvar, Mutex};

use crate::config::BUFFER_SIZE;
use crate::ops::stream::TransferOutcome;

// Absorb short producer/consumer bursts in RAM before spilling. This is a
// per-stream bound, not an eager allocation; larger backlogs still use disk.
// A 32 MiB weather probe spilled 24--64 MiB per invocation with an 8 MiB
// cap, while the original unbounded queue stayed in RAM. Keep a fixed bound
// large enough for ordinary producer bursts; sustained backlogs still spill.
const MEMORY_LIMIT: usize = 64 * 1024 * 1024;

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

/// Create a single-producer channel. Dropping the sender signals EOF; dropping
/// the receiver cancels delivery. Spill files are unlinked immediately after opening.
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
    /// Queue bytes in order, returning false when the receiver has closed.
    pub(crate) fn send(&self, bytes: &[u8]) -> Result<bool> {
        let mut state = self.shared.state.lock().unwrap();
        if state.receiver_closed {
            return Ok(false);
        }
        // The receiver copies disk bytes into its own buffer before releasing
        // this mutex. Once all spill bytes have been consumed, that descriptor
        // can be dropped even if the destination write is still in progress.
        // Return to the bounded memory queue rather than spilling forever after
        // a temporary slow consumer. Pending disk bytes must retain FIFO order.
        if state.file.is_some() && state.consumed == state.written {
            debug_assert!(state.chunks.is_empty());
            state.file = None;
            state.written = 0;
            state.consumed = 0;
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
    /// Drain through EOF or the first destination error, then close the receiver.
    pub(crate) fn forward(self, mut destination: impl Write) -> Result<TransferOutcome> {
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
                    return Ok(TransferOutcome::Completed);
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
                    Ok(TransferOutcome::BrokenPipe)
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
        assert_eq!(receiver.forward(&mut output)?, TransferOutcome::Completed);
        fs::remove_dir(directory)?;
        assert_eq!(output, input);
        Ok(())
    }

    #[test]
    fn drained_spill_returns_to_memory_without_reordering() -> Result<()> {
        use std::sync::mpsc;
        use std::time::Duration;
        struct AcknowledgingWriter {
            bytes: Vec<u8>,
            threshold: usize,
            acknowledged: Option<mpsc::Sender<()>>,
        }
        impl Write for AcknowledgingWriter {
            fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
                self.bytes.extend_from_slice(bytes);
                if self.bytes.len() >= self.threshold {
                    if let Some(sender) = self.acknowledged.take() {
                        let _ = sender.send(());
                    }
                }
                Ok(bytes.len())
            }
            fn flush(&mut self) -> std::io::Result<()> {
                Ok(())
            }
        }
        let directory = std::env::temp_dir().join(format!("incr-spool-{}", rand::random::<u128>()));
        let (sender, receiver) = create(&directory);
        let initial = vec![17; MEMORY_LIMIT * 2 + 31];
        for chunk in initial.chunks(7777) {
            assert!(sender.send(chunk)?);
        }
        assert!(sender.shared.state.lock().unwrap().file.is_some());
        let (acknowledge, acknowledged) = mpsc::channel();
        let length = initial.len();
        let worker = std::thread::spawn(move || -> Result<Vec<u8>> {
            let mut output = AcknowledgingWriter {
                bytes: Vec::new(),
                threshold: length,
                acknowledged: Some(acknowledge),
            };
            assert_eq!(receiver.forward(&mut output)?, TransferOutcome::Completed);
            Ok(output.bytes)
        });
        // Even on timeout, drop the producer and join the receiver before
        // reporting the error so a failing test cannot leave a blocked worker.
        let received = acknowledged.recv_timeout(Duration::from_secs(3));
        let tail = b"after the temporary spill";
        if received.is_ok() {
            assert!(sender.send(tail)?);
            assert!(sender.shared.state.lock().unwrap().file.is_none());
        }
        drop(sender);
        let output = worker.join().unwrap()?;
        fs::remove_dir(directory)?;
        received?;
        assert_eq!(output, [initial.as_slice(), tail].concat());
        Ok(())
    }

    #[test]
    fn destination_errors_close_the_channel() -> Result<()> {
        struct FailingWriter(ErrorKind);

        impl Write for FailingWriter {
            fn write(&mut self, _: &[u8]) -> std::io::Result<usize> {
                Err(self.0.into())
            }

            fn flush(&mut self) -> std::io::Result<()> {
                Ok(())
            }
        }

        for error in [ErrorKind::BrokenPipe, ErrorKind::PermissionDenied] {
            let (sender, receiver) = create(Path::new("unused-spool-directory"));
            assert!(sender.send(b"queued")?);
            let result = receiver.forward(FailingWriter(error));
            if error == ErrorKind::BrokenPipe {
                assert_eq!(result?, TransferOutcome::BrokenPipe);
            } else {
                assert!(result.is_err());
            }
            assert!(!sender.send(b"after failure")?);
        }
        Ok(())
    }

    #[test]
    fn concurrent_delivery_and_empty_eof_complete() -> Result<()> {
        for count in [0, 1, 128] {
            let (sender, receiver) = create(Path::new("unused-spool-directory"));
            let producer = std::thread::spawn(move || -> Result<()> {
                for sequence in 0..count {
                    assert!(sender.send(&[sequence as u8; 97])?);
                    std::thread::yield_now();
                }
                Ok(())
            });
            let mut output = Vec::new();
            assert_eq!(receiver.forward(&mut output)?, TransferOutcome::Completed);
            producer.join().unwrap()?;
            let expected: Vec<_> = (0..count).flat_map(|sequence| [sequence as u8; 97]).collect();
            assert_eq!(output, expected);
        }
        Ok(())
    }
}
