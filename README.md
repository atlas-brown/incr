# incr

Bolt-on incremental execution for the shell. Caches command outputs and reuses them when inputs haven't changed.

## Quick Start

```bash
# Build incr and observe (observe is optional but recommended for write commands)
cargo build --release
cd ../observe && cargo build --release && cd ../incr

# Run a script with incremental execution
./incr.sh my_script.sh [/path/to/cache]
```

When **observe** is built as a sibling project (`../observe/target/release/observe`), incr.sh automatically uses it for write commands, avoiding the sandbox setup used by the fallback mode (try + strace). incr works without observe; it falls back to try + strace for write commands.

---

## Usage

### Script mode (recommended)

Transform and run a bash script so each command is executed incrementally:

```bash
./incr.sh <script> [cache_dir]
```

- **script**: Path to your bash script
- **cache_dir**: Optional; defaults to `/tmp/incr_cache` (or set `INCR_CACHE_DIR`)
- **observe**: Auto-enabled when `../observe/target/release/observe` exists

incr.sh uses `insert.py` to wrap each command with incr, then runs the transformed script. Re-run the script; unchanged commands replay from cache.

### Direct command mode

Run a single command through incr:

```bash
./target/release/incr --try ./src/scripts/try.sh --cache /tmp/my_cache [--observe ../observe/target/release/observe] -- <command> [args...]
```

Example:

```bash
# Read-only (uses TraceFile)
echo "" | ./target/release/incr -t ./src/scripts/try.sh -c /tmp/cache --observe ../observe/target/release/observe -- cat input.txt

# Write (uses Observe when --observe is passed)
echo "" | ./target/release/incr -t ./src/scripts/try.sh -c /tmp/cache --observe ../observe/target/release/observe -- bash -c "echo hello > output.txt"
```

---

## Using observe

**observe** is a lightweight ptrace-based tracer that records file reads/writes. incr uses it instead of strace + the try filesystem sandbox for commands that write files.

### Why use observe?

Observe traces commands on the live filesystem, avoiding the fallback's per-command
mergerfs sandbox setup. This also preserves live shared-file and FIFO interactions.
Actual speedups depend on the workload and whether its effects can safely replay;
see the minimum-input qualification results under `qualification/results/`.

### Enabling observe

1. **Build observe** (sibling to incr):
   ```bash
   cd ../observe && cargo build --release
   ```

2. **Script mode**: incr.sh auto-detects `../observe/target/release/observe` and passes it to insert.py. No extra flags.

3. **Direct mode**: Pass `--observe ../observe/target/release/observe` (or the full path) to the incr binary.

### When observe is used

- **Write commands** (echo > file, cp, sed -i, etc.): Use Observe mode (replaces Sandbox)
- **Known read-only tool forms** (e.g. cat or head): Use TraceFile with observe for lighter tracing
- **Known stream-only system-tool forms** (e.g. stdin-only `rev`): No tracing

### Fallback: try + strace

When observe is **not** available (not built or not passed via `--observe`), incr falls back to **try + strace**:

- **Write commands**: Run inside a **try** filesystem sandbox. The command executes in an isolated overlay; strace records file access; try commit applies changes to the real filesystem. Requires `mergerfs` (or `unionfs`) and `try.sh`.
- **Read-only commands**: Use **strace** to trace file reads (TraceFile mode). No sandbox.
- **Known stream-only system-tool forms**: No tracing (Nothing mode).

This fallback works without the observe project. It adds sandbox setup and commit overhead. Use it when Observe is unavailable; its overlay is not a security boundary.

---

## Cache correctness and execution limits

Incr reuses deterministic command output when its arguments, environment, working
directory, executable identity, umask, stdin and recorded filesystem dependencies match. Observe reports
first-access state, including failed opens, symlinks, directories and write targets.
File state includes ctime as well as mtime, size and mode. `/tmp` inputs are tracked.
Static tool annotations apply only to resolved system tools, so custom PATH programs
with the same names are traced. Commands using inherited extra file descriptors or non-UTF-8 arguments/environment
execute directly. Unrepresentable dependency paths prevent reuse.

Streaming execution starts the command while consuming stdin. An effect gate lets
Incr cancel and replay only before Observe permits the first live write. After that
point the command finishes normally, without rollback or a second application of
its writes. Batch mode requires finite stdin and checks the cache before execution.
Cache writers use a nonblocking per-entry lock; competing invocations execute with
private temporary entries instead of waiting on each other.

Regular-file content, modes, empty directories and symlinks can replay after all
saved payloads have been validated. Operations requiring inode or metadata history
(rename, unlink, hard-link creation, ownership/timestamp changes and special-file
creation) currently force live execution. This is conservative: it preserves those
operations but reduces warm-run reuse. Cache key version 12 and Observe dependency
protocol 3 invalidate incompatible entries. External network state, clocks, random
sources and arbitrary concurrent changes are not general memoization inputs.

The wrapper creates an owned transformed copy and never rewrites the input script.
Use `INCR_CACHE_DIR=/path/to/cache ./incr.sh -b script.sh args...` for the Bash parser
and unambiguous script arguments. Source/history introspection and interpreter modes
that cannot preserve semantics through transformation execute natively. Those paths
are correct passthroughs, not accelerated cases. Parser source locations can refer
to the private transformed copy. Set `INCR_OBSERVE=0` to force try/strace, or `1` to
require Observe; `INCR_OBSERVE_PATH` selects its executable.

## Development Setup

1. **Rust**: Install Rust (e.g. `rustup`).
2. **OverlayFS**: `sudo apt install mergerfs` (for try.sh sandbox when observe is not used).
3. **Python**: For `insert.py` (script transformation):
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Build**:
   ```bash
   cargo build --release
   ```

Toggle `DEBUG` and `DEBUG_LOGS` in `src/config.rs` for cache debug info and logs.

### Docker

```bash
docker build -t incr .
docker run -it --rm -v $(pwd):/app --privileged incr
```

---

## Testing and benchmarks

```bash
# Integration tests (incr + observe)
bash agents/test_incr_observe.sh

# Benchmark: strace vs observe
bash agents/run_bench.sh
python3 agents/benchmarks/plot.py agents/benchmarks/results.txt   # requires matplotlib
```

See `agents/README.md` for details.

---

## Evaluation suite

The `evaluation/` directory contains Koala-style benchmarks. **Entry point:** `evaluation/benchmarks/run_all.sh` (or `evaluation/run.sh`, which forwards arguments).

```bash
# EASY suite (12 benchmarks), min inputs: bash + incr (try+strace) + incr-observe
bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all

# War-and-peace (word count pipeline)
bash evaluation/war-and-peace/with_cache.sh
bash evaluation/war-and-peace/with_cache_observe.sh
bash evaluation/war-and-peace/without_cache.sh
```

Results: `evaluation/run_results/<min|small>/`. See `evaluation/README.md` and `agents/docs/EVALUATION_BENCHMARK_SUITE.md`.

For Koala upstream scripts, clone https://github.com/kbensh/koala and manually insert `target/release/incr` invocations where needed.
