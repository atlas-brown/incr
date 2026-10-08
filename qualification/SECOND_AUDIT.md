# Second audit and fast qualification

Scope: correctness, edge cases, bounded stress, performance opportunities and code
quality in both runtime codebases. No real-model runs or full benchmark matrix.

## Execution

- Review all runtime modules, prioritizing resource ownership, cache validity,
  syscall coverage, snapshot/replay and shell transformation.
- Keep components small and composable; use descriptive names and concise comments.
- Add tiny deterministic reproductions before fixes. Use process-tree deadlines:
  5 seconds per ordinary case, 30–60 seconds per focused group, and an explicit
  bound for the complete fast matrix. Stop and diagnose the first unexpected failure.
- Rebuild only after coherent edits; run focused tests first, then the fast matrix.
- Record findings, regressions, stress counts and limits here and in QUALIFICATION_LOG.md.
- Clean owned artifacts, commit relevant changes with subject-only messages and
  push Observe main and Incr observe. Preserve the previous measurement evidence.

## Coverage

| Area | Status | Findings |
|---|---|---|
| Incr cache/dependencies/effects | Reviewed | Fixed hard-link preflight, directory-to-file child absence, read-only replay and permission cleanup; fixed low-descriptor restoration and parent-symlink hard-link alias replay; parent access and unchanged-inode retargeting tested; group-writable replay preserves ownership |
| Incr stream/batch/chunk execution | Reviewed | Extracted speculative restoration; fixed terminal stdin loss; 16 mode variants and chunk tests pass at checkpoints; final rerun passed |
| Incr process ownership/buffering | Reviewed | Cancellation, early consumers, 12-way shared cache contention, receiver errors and spill boundaries covered by bounded tests |
| Incr annotations/config/CLI | Reviewed | Literal argv, byte executable/cwd keys, PWD cache invalidation and terminal handling fixed; annotation argument restrictions and chunk eligibility reviewed |
| Incr shell/trace parsers | Reviewed | Structured shell prefix nodes; binding collection; preserved-source execution; eight focused cases and 23 Bash differential cases pass; trace parser strict decoding reviewed |
| Observe syscall handling | Reviewed | Split open, metadata and directory-entry handlers; consolidated hashing; captured open flags once; fixed O_PATH write classification |
| Observe tracer/process lifecycle | Reviewed | Split event transitions from wait/termination; stop/exit state ownership and unknown-register failures audited; full integration rerun passes |
| Observe paths/dependencies | Reviewed | Fixed rooted join and lossy Unix path handling; lossless protocol 7, byte restoration, direct/chained parent-link dependency tests pass |
| Observe snapshots | Reviewed | Dedicated Snapshot component; payload preflight, byte paths, failure records, read-only restoration and parent-link retarget restoration tested |
| Observe output/seccomp/gate | Reviewed | Reporting separated from CLI; gate attachment/cancellation contract reviewed; seccomp branch offsets bounded; integration coverage includes gate and ABI cases |

Final qualification passed and runtime commits are published. See results/second-audit/REPORT.md for final evidence.

## Path handling and quoting

Explicit user requirement: remove ad hoc path/string escaping hacks and replace them
with correct implementations. Audit the boundaries between filesystem paths, shell
arguments, strace text, JSON and Unix byte strings. Prefer Path/PathBuf/OsStr and
structured process arguments; use a real format parser when textual decoding is
unavoidable. Test spaces, quotes, backslashes, newlines, Unicode, shell metacharacters,
symlink parent traversal, and literal names resembling tracer annotations. Keep
unsupported byte sequences explicit rather than silently rewriting or dropping paths.

Organization and documentation: module moves, new abstractions and file removal are
in scope when they simplify responsibilities. Add concise API documentation covering
contracts, ownership/cleanup, failure behavior and assumptions. Remove redundant
narration, but do not leave non-obvious interfaces undocumented. Preserve useful
historical evidence; distinguish generated runtime artifacts from intentional records.

## Latest checkpoint

- Observe uses dependency protocol 7 and lossless paths. Incr uses cache version 22;
  cache encoding restrictions no longer masquerade as unrecoverable trace effects.
- Streaming replay is tested with unexpected temporary UTF-8 and byte paths,
  including byte paths reached through a parent symlink. Manifests retain the
  logical-to-physical mapping used during capture.
- Current focused checks: 28 Incr units, 15 Observe path/open/permission cases,
  57 Incr regressions and 407 Observe top-level integration assertions. The exact
  source points and reruns are recorded in the work log and result JSON files.
- Final fast matrix, lightweight measurements, artifact cleanup and runtime publication completed.
- Low-descriptor sibling-file and nested-directory tests pass after scoping
  permission guards. Cancellation is covered in the matrix and Observe suite.
- Parent-link tracking is now explicit. Finish ordinary-directory replacement,
  end-to-end invalidation checks now pass, including unchanged leaf inodes. Parent
  mode/ownership/effective-access dependencies avoid self-invalidating timestamps.

## Cross-mode checkpoint

All 16 policy/executor/compression variants passed. The subsequent chunk group
exposed a test-environment mismatch after PWD became part of the command key;
all nine chunk groups pass with matching environments. The final matrix subsequently passed after cleanup. It now includes the parent-link
streaming restoration probe. Low-descriptor tests cover 80 sibling files and
80 read-only two-level directory trees.

## Repository organization

Observe now separates reports, tracer events, syscall families, snapshot capture,
restoration and shared permission operations. Incr separates speculative rollback
from streaming orchestration and effect tests from production replay code. Shell
transformation uses parsed prefix words and a binding collector rather than
synthetic string words and a discarded transformation pass.

Removed the unused main/ tree: 620 files, 58,338,809 bytes, including 569 files
identical to active counterparts. Remaining differences were retired runners and
fixtures; the inventory records hashes and counterparts. Active evaluation and
qualification paths remain. Removed unused word-frequency generator calls and
updated historical-tool documentation. The benchmark component suite passes.

## Completion

All 28 final groups, 23 Bash cases and 54 measurement runs passed. Runtime fixes
are published in both repositories; the accompanying evidence commit contains
the final report, source fingerprints, measurements and cleanup record.
