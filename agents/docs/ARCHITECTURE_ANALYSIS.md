# incr Architecture: Trace Modes, Executors, and Optimizations

This document explains how incr's trace modes, stream vs batch executors, and pure/stateless optimizations work. For observe integration and fallback (try + strace), see main `README.md` and `FINDINGS.md`.

---

## 1. High-Level Flow

```
incr.sh
  └─> insert.py transforms script (adds incr --try --cache [--observe] to each external command)
  └─> bash runs instrumented script
        └─> each command: incr --try <path> --cache <dir> [--observe <path>] <cmd> <args>
              └─> main.rs: parse_input, choose executor, execute
```

**Executor selection** (main.rs L76-84):
1. **Chunk executor** — if `enable_annotations` AND `check_stateless(command)` AND not `full_tracing`
2. **Stream executor** — if NOT `batch_executor` (default)
3. **Batch executor** — if `batch_executor` (CLI `-b`)

---

## 2. Trace Modes (TraceType)

Trace type is chosen by `get_trace_type(cache_directory, command, observe_command)` in [incr/src/execution/mod.rs](incr/src/execution/mod.rs):

| Order | Condition | TraceType |
|-------|-----------|-----------|
| 1 | `check_pure(command)` | **Nothing** |
| 2 | `check_stateless(command)` OR `check_read_only(command)` | **TraceFile** |
| 3 | `get_introspect_file(...).exists()` | **TraceFile** |
| 4 | `observe_command.is_some()` | **Observe** (replaces Sandbox for writes) |
| 5 | (default) | **Sandbox** (fallback: try + strace) |

**Fallback**: When observe is not available, write commands use Sandbox (try overlayfs + strace). See main `README.md`.

### 2.1 TraceType::Nothing

- **When:** Commands in PURE_COMMANDS (basename, cut, grep, rev, sort, tr, uniq)
- **Execution:** Run command directly, no tracing
- **Cache key:** Command + args + env + stdin_hash only (no file dependencies)
- **Rationale:** These commands are deterministic from stdin; no file I/O to track

### 2.2 TraceType::TraceFile

- **When:** READ_ONLY_COMMANDS (awk, cat, comm, find, head, paste, sed, tail), STATELESS_COMMANDS (empty), or we have introspect data from a previous run
- **Execution:** When observe available: `observe --json --output <file> --no-filter -- <cmd>`. Else: `strace -yf --seccomp-bpf --trace=fork,clone,%file -o <trace_file> -- <cmd>`
- **No sandbox:** Writes go to real filesystem (but these commands shouldn't write)
- **Trace file:** Written to cache dir (batch) or temp path (stream); `.json` → parse_observe, else → parse_strace
- **After run:** Parse trace for read/write sets; no commit needed

### 2.3 TraceType::Observe

- **When:** Commands that may write AND `observe_command.is_some()` (--observe passed)
- **Execution:** `observe --json --output <file> --no-filter -- <cmd>` (no sandbox)
- **Trace file:** JSON in cache dir (e.g. `observe_{key}.json` or `batch_<hash>/observe.json`)
- **After run:** `capture_observe_output()` copies written files to `outputs/upperdir`, then `try commit` applies changes
- **Benefit:** ~10x faster than Sandbox for write commands; no overlayfs overhead

### 2.4 TraceType::Sandbox (fallback)

- **When:** Commands that may write AND observe is NOT available
- **Execution:** `try -D <sandbox_dir> strace -yf ... -o /tmp/trace.txt -- <cmd>`
- **Sandbox:** try creates overlayfs; all writes go to `sandbox/upperdir/`
- **Trace file:** Inside sandbox at `upperdir/tmp/trace.txt` (strace -o writes there)
- **After run:** `extract_sandbox_output()` moves upperdir to `outputs/upperdir`, then `try commit` applies changes to real filesystem

---

## 3. Annotation System

[annotation/mod.rs](incr/src/annotation/mod.rs) and [annotation/rules.rs](incr/src/annotation/rules.rs):

| Check | Purpose | Commands |
|-------|---------|----------|
| `skip_command` | Don't run through incr at all; exec directly | IGNORE_COMMANDS (built-ins: cd, echo, exit, etc.; metadata: chmod, touch, etc.) |
| `check_pure` | TraceType::Nothing | PURE_COMMANDS: basename, cut, grep, rev, sort, tr, uniq |
| `check_stateless` | TraceType::TraceFile | STATELESS_COMMANDS (empty list) |
| `check_read_only` | TraceType::TraceFile | READ_ONLY_COMMANDS: awk, cat, comm, find, head, paste, sed, tail |

**Condition matching:** Each command has `disallowed_flags` and `max_arguments`. A command matches only if it has no disallowed flags and ≤ max_arguments.

---

## 4. Executors in Detail

### 4.1 Batch Executor

**When:** `-b` flag passed to incr

**Flow:**
1. Read stdin to end
2. Compute cache key: command + args + env + stdin_hash → `batch_<hash>/`
3. Check cache: load data, `check_cache_valid` (read deps unchanged?)
4. **Cache hit:** Output cached stdout/stderr, run `try commit` if there were writes
5. **Cache miss:** Spawn command, wait for exit, parse trace, extract sandbox, commit, save

**Key:** Cache directory is known *before* running (from stdin hash). Single run, full stdin available.

### 4.2 Stream Executor

**When:** Default (no `-b`)

**Flow:**
1. Spawn command immediately (don't wait for stdin)
2. **Parallel:** Thread 1 hashes stdin while forwarding to child; threads 2–3 capture stdout/stderr
3. Cache key depends on stdin hash — computed on the fly
4. **Early cache check:** After stdin is fully read/hashed, check if cache exists and is valid
5. **Cache hit:** Kill child, clean temp files, output cached data, commit if needed
6. **Cache miss:** Wait for child, parse trace, extract sandbox, commit, save, move temp files to final cache dir

**Key difference:** Uses random temp paths (`stdout_<key>.incr`, `trace_<key>.txt`, `sandbox_<key>`) first, then renames to `batch_<hash>/` after we know the stdin hash. This allows starting the command before stdin is fully consumed.

### 4.3 Chunk Executor

**When:** `enable_annotations` AND `check_stateless(command)` AND not `full_tracing`

**Flow:**
1. **TraceType::Nothing only** — `create_child_runtime` asserts `trace_type == Nothing`
2. Chunks stdin by lines (LineChunker, CHUNK_GRANULARITY)
3. For each chunk: spawn command, forward chunk to stdin, hash chunk
4. If chunk cache exists for that hash: kill child, output cached chunk
5. Else: wait for child, save stdout/stderr to chunk dir
6. Worker pool processes multiple chunks in parallel

**Key:** For stateless commands (e.g. `grep`), output for chunk N depends only on chunk N's stdin. No file dependencies. Cache key: `chunk_<cmd_hash>/chunk_<stdin_hash>/`.

**Note:** STATELESS_COMMANDS is empty, so chunk executor is currently never used unless annotations are extended.

---

## 5. RuntimeType and spawn_child

[command.rs](incr/src/command.rs) `spawn_child`:

| RuntimeType | Shell command | Args |
|-------------|---------------|------|
| Sandbox(dir) | try | `-D <dir> strace -yf --seccomp-bpf --trace=fork,clone,%file -o /tmp/trace.txt -- <cmd>` |
| TraceFile(file) | strace or observe | strace: `-o <file> -- <cmd>`; observe: `--json --output <file> --no-filter -- <cmd>` |
| Observe(file) | observe | `--json --output <file> --no-filter -- <cmd>` |
| Nothing | command.name | `<cmd> <args>` |

**Output capture:** All modes capture stdout/stderr to files via `capture_stream`, which also forwards to the real stdout/stderr (with optional `destination_ready` gating for short-circuit).

---

## 6. Pure Command Optimization (skip_executor)

**When:** `!full_tracing && skip_command(command, environment)`

**Action:** `exec` the command directly — replace incr process with the command. No caching, no tracing. Used for:
- IGNORE_COMMANDS (built-ins, metadata commands)
- Commands that are bash function overrides (`BASH_FUNC_*%%` in env)

---

## 7. Stream Executor: destination_ready and Short-Circuit

**ReadySignal:** Controls when captured output is forwarded to the real stdout/stderr.

- **AlwaysReady (batch):** Always forward immediately
- **SignalReceiver (chunk):** Wait until `signal_ready()` — used to order chunk output

**Short-circuit:** If downstream closes the pipe (e.g. `head` stops reading), `capture_stream` detects BrokenPipe. With `config.short_circuit`, it returns `BrokenPipe` immediately and the executor exits with `BROKEN_PIPE_CODE` instead of waiting for the full command.

---

## 8. Dependency and Cache Validation

**Read dependencies** (from parse_trace read_set):
- `DoesNotExist` — file must not exist
- `Timestamp` — file mtime must match
- `Hash` — file content hash must match (used when file was also written by this command)

**filter_dependencies:** Removes paths under DYNAMIC_EXCLUDED_PATHS (`/tmp`) when the dep is DoesNotExist and the path doesn't exist. Avoids cache invalidation from transient /tmp files.

**Introspection:** After each run, `save_introspection` creates `introspect/command_<hash>.incr` if the command had *no* writes, or removes it if the command wrote. So introspect file exists = "we've seen this command and it was read-only." On the next run, `get_introspect_file(...).exists()` → TraceFile. We avoid Sandbox overhead for commands we've already observed to be read-only.

---

## 9. Cache Layout

**Batch/Stream (batch_cache):**
```
batch_<hash>/
  data                    # CacheData (bincode)
  stdout.incr
  stderr.incr
  observe.json            # (Observe mode) trace file; or trace_{key}.txt (TraceFile)
  sandbox/                # (Sandbox mode only) try overlay
    upperdir/
      tmp/trace.txt       # strace output
    ignore
  outputs/                # (after extract_sandbox_output or capture_observe_output)
    upperdir/             # files to commit
    ignore
```

**Chunk (chunk_cache):**
```
chunk_<cmd_hash>/
  chunk_<stdin_hash>/
    stdout.incr
    stderr.incr
```

---

## 10. Summary Table

| Aspect | Batch | Stream | Chunk |
|--------|-------|--------|-------|
| When | `-b` | default | stateless + annotations |
| Stdin | Read all first | Stream + hash in parallel | Chunk by lines |
| Cache path | Known upfront | Temp then rename | Per-chunk |
| Trace modes | All | All | Nothing only |
| try/sandbox | Yes (Sandbox) | Yes (Sandbox) | No |

| TraceType | Tracing | Sandbox | Commit |
|-----------|---------|---------|--------|
| Nothing | none | no | no |
| TraceFile | strace or observe | no | no |
| Observe | observe | no | try commit |
| Sandbox | strace (in try) | yes (try) | try commit |
