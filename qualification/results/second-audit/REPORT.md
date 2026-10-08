# Second audit qualification

Runtime changes are committed and pushed to Incr `observe` and Observe `main`:

- incr: `8f3c769cedfd22c4d3612560921661ff67665478`
- observe: `b5ad47a8d6155559d01f0fca616e72ab19d749e6`

## Changes

Fixed cache validity for parent permissions, symlink retargeting and PWD; replay
of read-only and group-writable files; hard-link alias handling; descriptor
exhaustion; terminal input; and shell-prefix quoting. Observe now transports Unix
paths losslessly and records parent traversal dependencies. Unsupported cache path
encodings execute without persistence instead of reusing a lossy key.

Separated snapshot capture/restoration, permission operations, tracer events,
syscall families and reporting in Observe. Incr now separates speculative rollback
and replay tests, and shell transformation uses parsed arguments and binding
collection. Added concise contract documentation and descriptive names. Removed
620 unused files from the duplicate main/ tree; the inventory preserves hashes
and counterpart information. Active benchmark paths remain intact.

## Final validation

- 28/28 bounded qualification groups passed in 198.9 seconds: 16 live/final,
  streaming/batch, compression and annotation variants, plus focused suites.
- 23 Bash cases, 46 native/candidate executions, matched in 88.9 seconds.
- Incr: 28 ordinary Rust tests passed; the normally ignored foreign-owner test
  was explicitly run and passed in the matrix. Observe: six Rust tests passed.
- Observe integration suite: 36 files and 407 assertions passed.
- Both repositories passed formatting, strict Clippy and whitespace checks.
- Stress coverage includes low descriptor limits, 80 sibling files, 80 nested
  read-only directory trees, shared-cache contention, cancellation, early consumers,
  spill boundaries, and streaming restoration through byte paths and parent links.
- Final matrix and Bash supervisors reported no timeouts or leaked descendants.

Source and binary hashes are in [final-build.json](final-build.json). Exact
results are in [matrix](final-matrix/summary.json), [Bash](final-bash/summary.json)
and [qualification-summary.json](qualification-summary.json). Earlier failed
reproductions/checkpoints are retained as diagnostic evidence, not final passes.

## Minimum-input measurements

All 54 executions matched Bash stdout, exit status, normalized stderr and
filesystem manifests. Each workload used three repetitions per mode and phase.
Observe used final-output effect policy. Comparison is against the current try
backend, not a new timing run of the historical main commit.

| Workload | Phase | Bash seconds | Try seconds | Observe seconds | Try / Observe |
|---|---|---:|---:|---:|---:|
| file-mod/file-mod-1.sh | cold | 0.242 | 2.290 | 0.598 | 3.83× |
| file-mod/file-mod-1.sh | warm | 0.266 | 2.260 | 0.253 | 8.93× |
| word-freq/top-n.sh | cold | 1.888 | 2.434 | 1.536 | 1.58× |
| word-freq/top-n.sh | warm | 1.719 | 2.276 | 0.295 | 7.72× |
| word-freq/wf.sh | cold | 1.571 | 2.231 | 1.458 | 1.53× |
| word-freq/wf.sh | warm | 1.489 | 2.083 | 0.303 | 6.88× |

Values are medians. Geometric-mean speedups are 2.10× cold and
7.80× warm. Word-frequency uses the existing 10,485,770-byte minimum
input; conversion uses songs.min. This is a three-workload sample, not a full-suite
performance claim. See [statistics](measurement-statistics.csv) and
[raw run summary](measurements/summary.json). Earlier full minimum-suite evidence
remains in ../2026-10-08/EVALUATION.md.

## Limits and cleanup

Both live and final policies passed correctness tests; performance figures above
use final-output assumptions. Non-UTF-8 paths are traced/restored losslessly but
cannot currently be persisted by the cache encoding. Snapshots do not promise
inode identity, all extended attributes or transactions against external writers.
Exact rollback of another owner's modified mtime requires OS privilege. Full-size
and model workloads were not rerun in this fast round; the API-key workload remains
skipped at the user's request.

Removed 583,377,839 logical bytes of disposable fixtures, caches and an intermediate
build snapshot. Reusable dependencies and qualified build snapshots remain.
[cleanup.json](cleanup.json) records exact paths and confirms no owned temporary
fixture paths remained. Historical measurement records were preserved.
