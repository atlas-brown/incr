//! Shared outcomes for forwarding input and replaying captured output.

/// A closed destination is distinct from an I/O failure. Executors decide whether
/// to finish capturing effects or stop early according to their output policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TransferOutcome {
    Completed,
    BrokenPipe,
}
