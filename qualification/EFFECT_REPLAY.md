# Effectful streaming replay investigation

Status: implemented and qualified on the minimum-input matrix. Final evidence is in
`results/2026-10-08/`; the earlier Incr 7990ee6 / Observe b993d58 baseline is preserved.

## User-authorized contract

Aggressively install cached contents when correctness can be established under an
explicit final-output assumption. Intermediate regular-file observations need not
be preserved under that policy. Keep a live-interaction policy for programs whose
correctness depends on shared-file/FIFO handshakes. Never describe final-output
parity as proof of arbitrary interaction equivalence.

## Baseline limitation

The baseline stream executor starts a child before it finishes hashing stdin. It validates
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

Implemented approach 1: it validates original state while retaining continuous
execution and streaming without waiting at an effect boundary. The alternatives
remain comparisons, not implemented guarantees.

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


## Development findings and retained limits

The first prototype implements candidate validation before execution with a
separate `--effect-policy final` cache namespace. Final is now the binary default;
select `--effect-policy live` explicitly for intermediate-effect semantics. The clean
full Bash evaluation is maintained in `../studies/bash-parity-audit-2026-10-08/`. On the deterministic early-write probe, overwrite and rename/unlink
warm runs retain cache metadata and drop from roughly 0.45s to 0.13s. Focused policy, chunk, compression and lifecycle tests pass; exact run counts
and evidence are tracked in QUALIFICATION_LOG.md. They do not close the cases below.

- Directory metadata invalidation: an interpreter reading its script directory
  can invalidate a candidate when that same directory contains changing outputs.
  Keep metadata correctness; investigate precise dependency semantics rather than
  silently ignoring directory timestamps.
- Final-state replacement now distinguishes overwriting an inode from replacing a
  pathname. External hard-link regression tests cover both cases.
- Partial reports must account for speculative temporary paths absent from the
  cached write set. Newly created paths are cleaned; unexpected preexisting writes
  now use selective pre-write restoration with tested contents/mode/mtime recovery.
- Candidate validation considers eight recent inputs and bounds hint retention to
  64 entries. Held cache leases protect selected payloads; concurrent
  cache qualification passes in the final fast matrix.
- Capture/replay is shared by batch and streaming, and wrapper policy selection
  is available. Completed module-level cleanup is tracked in CODE_REVIEW.md.


## Selective restoration during cancellation

A speculative execution can touch a preexisting temporary path that the cached run
did not touch, then normally restore it before finishing. Final outputs can still
be deterministic even when those intermediate paths vary. Cancelling after that
write requires restoring its original contents, mode and mtime. The selective
snapshot implementation now does this; speculative_restore_test.py forces the
intermediate write only during warm execution and verifies repeated actual hits.

Implemented: enable pre-write snapshots only when prevalidated candidates
exist. Exclude exact paths common to every candidate's write set, since the selected
cache entry will install their final state. Other paths are captured before effects. Stop
and reap all writers, restore the speculative snapshots, then install the selected
cached output. Exclusion must use the intersection of candidate paths, not their
union, because the stdin hash has not selected a candidate yet. Tests cover preexisting
contents, metadata and new temporary paths. Exclusions use exact paths shared by
all candidates. Failed restoration retains a recovery snapshot and reports an
error. This is confined to the explicit final-output policy.
