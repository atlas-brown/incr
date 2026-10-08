# Optimization contracts and coverage

The final benchmark matrix measures Observe with `--effect-policy final`. The
fast matrix tests both `live` and `final`. These policies answer different needs;
final-state equivalence does not establish equivalence for intermediate observers.

| Optimization | Contract and implementation | Qualification |
|---|---|---|
| Streaming | Start execution before stdin ends; hash while forwarding, with a 1 MiB memory queue and anonymous disk spill | Slow readers, early exit, infinite producers, spill cleanup |
| Live replay | Cancel only before the first live effect; execute commands that need FIFO or shared-file interactions | FIFO regressions and the effect probe's producer/writer handshake |
| Final-output replay | Validate candidates before execution; select by full stdin hash; stop all writers before restoring speculative paths and installing cached outputs | Overwrite, rename, directory trees, changed stdin, older candidates, unexpected preexisting writes |
| Batch | Require finite stdin; share dependency validation, capture and replay with streaming | Both policies, with and without compression; stream-only cases explicitly skipped |
| Compression | Compress cached payloads while retaining integrity validation and output/status semantics | Streaming, batch, full-tracing and annotation combinations |
| Chunk reuse | Resolved system `cat` without arguments and restricted alphanumeric `tr`; preserve chunk boundaries, ordering and status | Nine chunk tests, including fragmented reads, corruption and early consumers |
| Text assumption | `--assume-text` permits line-wise `rev` only for NUL-free ASCII in the C/POSIX locale | Explicit ASCII case plus binary fallback coverage |
| Annotations and introspection | Restrict annotations to resolved system tools; a previous read-only witness does not authorize ignoring new effects | Shadowed tools, executable replacement, file arguments, default and full-tracing variants |
| Concurrent caches | Hold nonblocking leases while validating/replaying; contention cannot expose incomplete payloads | Shared-cache concurrency, parallel wrappers and corrupted payload tests |
| Short-circuit output | Handle closed consumers without hanging; preserve completed filesystem effects | Infinite producer and closed-output regressions, chunk early-consumer test |

`fast-matrix/summary.json` records the 24 qualification groups. Each invocation has
a process-tree deadline and records cleanup evidence. The complete Bash suite adds
83 differential shell cases. `CODE_REVIEW.md` records runtime module coverage.

Final-output replay assumes deterministic final outputs and no concurrent external
mutation. An observer waiting to see every intermediate write can distinguish replay
from live execution, even if final bytes match. Such workflows must use `live`.
Ownership, explicit timestamps, special files and other unsupported effects retain
replay barriers. Unchanged directory metadata is still a dependency: placing outputs
beside code can cause correct but avoidable misses. None of these assumptions is
silently relaxed to improve reported timings.

The minimum-size matrix is a correctness and overhead check. Its speedups do not
predict full-size performance, and real-model DPT uses single timing samples.
