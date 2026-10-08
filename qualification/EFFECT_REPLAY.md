# Effectful streaming replay investigation

Status: design and experiments pending implementation. This extends the frozen
qualification baseline at Incr 7990ee6 / Observe b993d58.

## User-authorized contract

Aggressively install cached contents when correctness can be established under an
explicit final-output assumption. Intermediate regular-file observations need not
be preserved under that policy. Keep a live-interaction policy for programs whose
correctness depends on shared-file/FIFO handshakes. Never describe final-output
parity as proof of arbitrary interaction equivalence.

## Current limitation

The stream executor starts a child before it finishes hashing stdin. It validates
a cache entry only afterward. Observe's effect gate prevents cancellation after
any effect starts, and replay barriers exclude unlink/rename operations entirely.
These rules preserve live interactions but also prevent useful final-output reuse.
A second problem is that late dependency checks see the running command's modified
files rather than their original input state.

## Approaches to compare

1. **Validate candidates before execution.** Maintain a bounded command-to-stdin-key
   index. Before spawning, validate candidate dependencies and hold their cache
   leases. Continue streaming normally. Once the complete stdin hash selects a
   prevalidated candidate, stop/reap the speculative process tree and install the
   cached final outputs under the final-output policy. Keep the original gate rule
   for live-interaction policy. Unselected candidates never authorize replay.
2. **Inspect state at an effect boundary.** Pause tracees and inspect their recorded
   first-access state before deciding whether to cancel. This avoids candidate
   indexing, but introduces a coordination protocol, multi-thread pause handling,
   and possible feedback-pipeline deadlocks. Any implementation needs bounded
   fallback to live execution rather than waiting for stdin while effects are held.
3. **Operation-level replay.** Record and replay remaining operations while accounting
   for the already-applied prefix. This can preserve more inode/interaction semantics
   but requires substantially more than a final-state manifest. Filesystem syscall
   coverage, interleaving and fd identity must be demonstrated, not assumed.
4. **Early complete-input lookup.** When all input is available immediately, look up
   before speculative execution. Useful supplementary optimization; it does not
   alone solve long streaming inputs or justify converting all execution to batch.

Start with approach 1 because it directly addresses original-state validation and
retains continuous execution/streaming without an effect-boundary wait. Treat this
as a hypothesis to test, not a completed design.

## Required safety and performance experiments

- Overwrite, append, read-modify-write, partial writes and stdin-dependent outputs.
- Creation, deletion, rename, directories, symlinks and hardlinks; verify final
  filesystem state and any explicitly retained identity/metadata guarantees.
- A writer that starts effects before EOF and then performs expensive work: prove
  real cancellation/cache reuse and speedup, not merely correct live reexecution.
- Input change before launch must invalidate; the command's own later write must
  not invalidate an otherwise valid prevalidated candidate.
- Multiple possible stdin keys and concurrent cache writers must not select stale
  or wrong entries, block each other, or expose partially replaced cache payloads.
- Speculative temporary files not present in the cached final state must be cleaned
  without erasing unrelated preexisting paths. Preserve evidence when capture fails.
- All writers/descendants must stop before installation. No zombie/mount leakage.
- FIFO communication, regular-file handshake and streaming early consumer exit
  must continue to work in live mode. Document final-mode counterexamples explicitly.
- Compression, short-circuiting, annotations and introspection must compose with
  the policy. Separate policy/cache formats so weaker cached assumptions cannot
  enter the stronger policy.

Use subsecond deterministic work in development tests, with process-tree deadlines.
Run real models only after the fast correctness/performance experiments stabilize.
