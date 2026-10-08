# Full source review tracker

Status is review coverage, not qualification. Pending entries remain required work.

| Repository / file | Status | Findings / next action |
|---|---|---|
| incr/src/annotation/mod.rs | Reviewed | Standard-tool checks gate pure/read-only/chunk annotations; chunk assumptions are explicit |
| incr/src/annotation/rules.rs | Reviewed | Conservative builtin/nondeterministic skip list; removed unused rule machinery |
| incr/src/cache/batch_cache.rs | Reviewed | Nonblocking leases, isolated contention entries, payload checks and commit errors audited; direct sandbox extraction avoids cross-filesystem rename; real streaming try test passes |
| incr/src/cache/candidates.rs | Reviewed | Bounded hint retention and validation; ignores unrelated entries; held leases prevent mutation; retention test passes |
| incr/src/cache/chunk_cache.rs | Removed | Consolidated onto shared validated, locked cache |
| incr/src/cache/effects.rs | Reviewed | Validates payloads before deletions, orders parents/links/permissions, distinguishes inode replacement from overwrite; alias regression and effect probes pass |
| incr/src/cache/mod.rs | Reviewed | Shared serialized dependency/result types and directory creation; no duplicate chunk schema |
| incr/src/command.rs | Reviewed | Managed child cleanup, consolidated spawning, pre-opened captures, bounded pending-output spool and signal statuses; 47 regressions and nine chunk tests pass |
| incr/src/config.rs | Reviewed | Explicit effect/text assumptions, bounded chunk constants; removed redundant comments and boolean expression |
| incr/src/effect_gate.rs | Reviewed | Atomic attachment/live/replay handshake with bounded attachment wait; mmap lifetime owned |
| incr/src/execution/batch_executor.rs | Reviewed | Shared capture/replay; completed effects survive drained output failure; cold/warm compressed and uncompressed regressions pass |
| incr/src/execution/chunk_executor.rs | Reviewed | Shared cache/replay, bounded worker pool, RAII completion/child ownership; nine behavioral tests and nonzero-status unit pass; long lines extend chunk boundaries but use disk spill instead of unbounded buffering |
| incr/src/execution/dependency.rs | Reviewed | Unified nanosecond metadata/ctime keys for try and Observe; unreadable captures cannot be reused; restored-mtime invalidation tested |
| incr/src/execution/mod.rs | Reviewed | Backend selection and trace filtering; final policy removes only rename/unlink barriers |
| incr/src/execution/record.rs | Reviewed | Shared capture requires initial write state, infers absent descendants, avoids replay on cold Observe execution and directly extracts try sandboxes |
| incr/src/execution/run.rs | Reviewed | Shared replay for all executors; broken pipe and oversized-prefix handling consistent; trace/sandbox cleanup remains explicit |
| incr/src/execution/skip_executor.rs | Reviewed | Shell-quoted native exec preserves skipped command semantics |
| incr/src/execution/stream_executor.rs | Reviewed | Prevalidated candidates, bounded spool, writer shutdown and selective snapshot restoration; timing-dependent preexisting write restores contents/mode/mtime with proven warm hits; recovery snapshots retained on failure |
| incr/src/main.rs | Reviewed | Independent default path resolution fixes relative cache paths; raw Unix fallback and child reaping retained |
| incr/src/ops/chunk.rs | Reviewed | Exact content boundaries independent of read sizes; line alignment and byte-size bounds tested; duplicate reference removed |
| incr/src/ops/data.rs | Reviewed | Removed unnecessary heap hashers; cache decoding capped at 64 MiB to reject oversized corrupt metadata |
| incr/src/ops/file.rs | Reviewed | Missing-file cleanup is idempotent; path conversion rejects non-UTF-8; no change needed |
| incr/src/ops/mod.rs | Reviewed | Debug logging no longer panics on missing directories or failed writes |
| incr/src/ops/serialize_bytes.rs | Reviewed | Human-readable optional bytes use base64; binary encoding preserves bytes; no change needed |
| incr/src/ops/thread.rs | Reviewed | Readiness predicate loops under mutex; scoped joins propagate panics with descriptive errors; chunk completion uses RAII |
| incr/src/scripts/incrementize.py | Reviewed | Shared parser setup, descriptive names, consolidated loop handling; generated prefix outputs checked |
| incr/src/scripts/insert.py | Reviewed | Consolidated Bash and Dash traversal; removed fixture-specific ignore names; Bash nested control flow and eight differential cases pass |
| incr/src/scripts/mod.rs | Reviewed | Exports the two active report parsers; no extra paths |
| incr/src/scripts/parse_observe.rs | Reviewed | Strict protocol 5 decoding; initial identity/state plus pre-write content hashes; unknown versions rejected |
| incr/src/scripts/parse_trace.py | Removed | Unused duplicate parser; repository runtime uses Rust parser |
| incr/src/scripts/parse_trace.rs | Reviewed | Removed warning suppression and duplicate wrappers; fixed path decoding, fork cwd and link/rename flags; seven unit and two real cache-hit/invalidation tests |
| incr/src/scripts/try.sh | Reviewed | Fixed commit status lost to pipeline subshell, saved ignore-list handling, temporary ignore cleanup and mount path quoting; four focused checks pass |
| observe/src/child.rs | Reviewed | ptrace/seccomp before initial stop and exec; conventional exec errors; removed redundant comments and short names |
| observe/src/dependency.rs | Reviewed | First-access file identity and symlink metadata captured; unsupported/non-UTF-8 state prevents reuse; protocol 5 tests pass |
| observe/src/effect_gate.rs | Reviewed | Skip repeat effect checks after live state; atomic arbitration preserved |
| observe/src/main.rs | Reviewed | Buffered typed reports avoid clones and tiny writes; raw Unix arguments preserved; existing format/exit/option tests pass |
| observe/src/proc_helpers.rs | Reviewed | Removed stale FD cache; O_PATH avoids blocking; preserved parent components and literal deleted suffix; bounded pathname read rejects partial strings |
| observe/src/seccomp.rs | Reviewed | Condensed filter builder; alternate ABI tag forces live execution; native 32-bit output and replay barrier tested |
| observe/src/snapshot.rs | Reviewed | Restoration phases handle nested rename and file/tree exchanges; failed open/rmdir preserve initial state; full Observe suite passes 405 assertions |
| observe/src/state.rs | Reviewed | Shared snapshot serialization and first-read dependency capture; removed descriptor cache state |
| observe/src/syscall.rs | Reviewed | Metadata, truncate, rename, xattr and async coverage audited; negative effects and failed snapshots fixed; unsupported effects carry barriers |
| observe/src/tracer.rs | Reviewed | Exec TID tracking, SIGTERM startup retry, ABI tag handling and bounded error-path child cleanup; signal/error/multiprocess checks pass |
| incr/src/scripts/shell_ast.py | Reviewed | Shared once-per-process libdash setup and version-conditional Shasta compatibility shim; generator and transformation tests pass |
| incr/src/ops/spool.rs | Reviewed | 1 MiB memory queue, anonymous disk spill, EOF and receiver-close ownership; order/cleanup and closed-receiver tests pass |
| incr/incr.sh | Reviewed | Removed unused argument array, installed cleanup before temporary setup, preserved native shell fallbacks; eight differential Bash cases pass |
