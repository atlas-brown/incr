//! Shared outcomes for forwarding input and replaying captured output.
use anyhow::Result;
use std::io::{ErrorKind, Write};
use std::sync::mpsc::Receiver;

/// A closed destination is distinct from an I/O failure. Executors decide whether
/// to finish capturing effects or stop early according to their output policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TransferOutcome {
    Completed,
    BrokenPipe,
}

/// Keep speculative stdin in memory, as in original Incr. Hashing must be able
/// to finish ahead of a slow child so a cache hit can cancel that child. Spilling
/// this queue to disk adds an unnecessary write of large pipeline intermediates.
pub(crate) fn forward_input(
    input: Receiver<Vec<u8>>,
    mut destination: impl Write,
) -> Result<TransferOutcome> {
    for bytes in input {
        if let Err(error) = destination.write_all(&bytes) {
            return if error.kind() == ErrorKind::BrokenPipe {
                Ok(TransferOutcome::BrokenPipe)
            } else {
                Err(error.into())
            };
        }
    }
    Ok(TransferOutcome::Completed)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc;

    #[test]
    fn input_preserves_binary_chunks_and_empty_eof() -> Result<()> {
        for chunks in [vec![], vec![vec![0, 255], vec![], vec![17; 8193]]] {
            let expected = chunks.concat();
            let (sender, receiver) = mpsc::channel();
            for bytes in chunks {
                sender.send(bytes)?;
            }
            drop(sender);
            let mut output = Vec::new();
            assert_eq!(forward_input(receiver, &mut output)?, TransferOutcome::Completed);
            assert_eq!(output, expected);
        }
        Ok(())
    }

    #[test]
    fn destination_failure_cancels_input_and_preserves_error_kind() -> Result<()> {
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
            let (sender, receiver) = mpsc::channel();
            sender.send(vec![1, 2, 3])?;
            let result = forward_input(receiver, FailingWriter(error));
            if error == ErrorKind::BrokenPipe {
                assert_eq!(result?, TransferOutcome::BrokenPipe);
            } else {
                assert_eq!(
                    result
                        .unwrap_err()
                        .downcast_ref::<std::io::Error>()
                        .unwrap()
                        .kind(),
                    error
                );
            }
            assert!(sender.send(vec![4]).is_err());
        }
        Ok(())
    }
}
