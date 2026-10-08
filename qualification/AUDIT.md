# Incr / Observe qualification audit

Scope: Linux x86-64, deterministic filesystem-oriented shell workloads, the 96
minimum-input benchmark entrypoints in `results/2026-10-07/inventory.json`, and
focused interaction/invalidation tests. Image annotation is excluded by the user;
full-size data is deferred. This is empirical qualification, not proof that arbitrary
programs are memoizable or that all bugs are absent.

## Purpose and backend semantics

Incr memoizes external commands within shell pipelines. The key includes command,
environment, working directory, executable identity, stdin and umask. It preserves incremental streaming:
a command starts while stdin is arriving, so a consumer that exits early must not
wait for the producer to close stdin. Batch mode intentionally requires finite input.
Safe static annotations can bypass tracing; dynamic read-only observations are not
proof that a later invocation cannot write. The baseline's stateless command table
is empty, so the chunk executor has no eligible commands in either branch.

Observe records filesystem accesses using ptrace/seccomp on the live filesystem.
That avoids the setup and deferred visibility of try's mergerfs sandbox. Cold effects
must remain live and must not be replayed after execution. A streaming cache hit can
cancel speculative work only before its first effect. The shared versioned gate
makes the cancellation/effect decision explicit. Once a write wins, live execution
finishes. FIFO/special-file dependencies prevent inappropriate reuse.

## Changes and evidence

| Area | Defect or risk addressed | Qualification |
|---|---|---|
| Initial state | Post-execution state cannot validate read/modify/write input | First-access protocol; repeated increment and append tests |
| Negative dependencies | Missing paths and dangling symlinks could be omitted | Failed-open, appearance and retarget tests |
| Write preconditions | Repeated mkdir/noclobber could replay success; partial writes could retain stale suffixes | Destination state recorded before all opens/creation; focused regressions |
| Input metadata | Restoring mtime could hide changed content | ctime, size and mode in dependency keys; preserved-mtime test |
| Live effects | Cold replay or speculative rollback could corrupt another command's files | No cold replay; effect gate; FIFO/shared-file tests |
| Replay scope | Final file bytes cannot reproduce rename/unlink/link/ownership semantics | Explicit replay barriers force live execution |
| Effects | Empty directories, symlinks and hardlink groups were incomplete | Typed versioned manifest; effect regressions |
| Corruption | Missing/corrupted saved payloads or output streams could be reused | All effect payloads and stdout/stderr hashed before replay |
| Contention | Two cache writers could replace each other's entries or deadlock | Nonblocking per-entry lock; private uncached entries; parallel test |
| Process ownership | Cancelled tracers could leave adopted descendants/zombies | Subreaper, kill/reap cleanup; bounded runner records survivors |
| Streaming | Producer keeping stdin open could hang an already-finished consumer | Polling stdin with child completion; early-exit and infinite-producer tests |
| Annotations | File-argument sort and general awk/sed were not safely pure | Narrow static rules, full-tracing override; file invalidation tests |
| Executable identity | A custom PATH could shadow a supposedly pure system tool; replacing a binary could retain a pure cache entry | Resolve the actual executable, restrict static annotations to system tools and include executable metadata in the key; PATH-shadowing and replacement tests |
| Ambient state | umask, inherited descriptors and Unix-byte paths were missing from safe reuse | umask key; direct execution for extra fds/non-UTF-8 argv/env; uncacheable lossy dependency paths |
| Wrapper | Rewriting caller scripts raced between invocations; eval changed Bash errors | Owned real transformed file; source-preservation and concurrent tests |
| Parsing | Locale escapes, source/history inspection and unknown commands changed semantics | Native passthrough for sensitive forms; 83-case Bash differential suite |

Compared with pinned main, the Observe branch retains the streaming/batch,
compression, annotation and short-circuit options. Main fixes for broken pipes and
sandbox extraction/commit cleanup were incorporated. Unsafe read-only assumptions
were narrowed instead of preserving incorrect reuse. `--full_tracing` actually
forces tracing, and `--skip_introspection` is respected on lookup. Main remains
unchanged in a detached worktree for measurement. It is not the correctness oracle;
Bash is, and identical failures never count as success.

## Benchmark repairs

- Beginner 13: `head 10` incorrectly treated 10 as a filename; use `head -n 10`.
- Bio 1: select the supplied minimum sample instead of a nonexistent hardcoded one.
- File-mod 7: archive the workload's WAV inputs rather than nonexistent gzip outputs
  from another script.
- Spell 6/7: sort and normalize the dictionary before `comm`; clean the owned file.
- Web search: create the output directory/index, avoid same-file read/truncate,
  handle absent index files, reject incomplete padded n-grams, and avoid the
  aggregate Natural import that emitted random dotenv messages into index data.
  A three-token golden test expects exactly six complete n-grams.
- DPT 5c/5d/5e: pass formatted classifications to the plotting helpers, and save
  the final PNG instead of waiting for a GUI. A synthetic format check supplements
  real-model end-to-end runs; it does not replace them.

## Limits that matter

Cache reuse assumes dependencies remain stable during validation/execution and
that external state is deterministic. Network services, clocks, randomness,
virtual filesystems and arbitrary concurrent external mutation are not a general
memoization contract. Known clock/random commands are bypassed, but that is not a
universal effect system. The try backend retains sandbox visibility differences;
Observe is the backend qualified for live communicating writers.

The replay manifest is not an operation log or an atomic multi-file transaction.
Operations requiring inode/metadata history run live. Access-time identity and
unusual filesystem coherence/privilege models are not covered by benchmark parity.
Stream capture still buffers input in memory; full-size memory/performance work is
explicitly deferred. Source-introspective Bash programs execute natively, so their
correctness does not imply acceleration. Wrapper diagnostics may name a transformed
source path and line; the differential harness normalizes only those locations.

The Bash harness compares actual captured test output, not run-driver diff status
against a vendored expected file from another Bash version. A few tests deliberately
leave background children; they pass only when native Bash does too and the bounded
supervisor cleans them. Benchmark runs do not allow leaked descendants. Each raw
record preserves the evidence, including failures and timeouts.
