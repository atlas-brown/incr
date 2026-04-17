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

When **observe** is built as a sibling project (`../observe/target/release/observe`), incr.sh automatically uses it for write commands, giving ~10x faster cold runs than the fallback mode (try + strace). incr works without observe; it falls back to try + strace for write commands.

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

**observe** is a lightweight ptrace-based tracer that records file reads/writes. incr uses it instead of strace + the try overlayfs sandbox for commands that write files.

### Why use observe?

| Mode | Write commands | Cold run | Warm run |
|------|----------------|----------|----------|
| **Fallback**: try + strace | Overlayfs sandbox + strace | ~250 ms | ~35 ms |
| **observe** | Direct execution + trace | **~23 ms** | **~18 ms** |

For write-heavy workloads, observe gives ~10x faster cold runs. The fallback (try + strace) uses full overlayfs isolation and works without building observe.

### Enabling observe

1. **Build observe** (sibling to incr):
   ```bash
   cd ../observe && cargo build --release
   ```

2. **Script mode**: incr.sh auto-detects `../observe/target/release/observe` and passes it to insert.py. No extra flags.

3. **Direct mode**: Pass `--observe ../observe/target/release/observe` (or the full path) to the incr binary.

### When observe is used

- **Write commands** (echo > file, cp, sed -i, etc.): Use Observe mode (replaces Sandbox)
- **Read-only commands** (cat, sed to stdout): Use TraceFile with observe for lighter tracing
- **Pure commands** (grep, wc): No tracing

### Fallback: try + strace

When observe is **not** available (not built or not passed via `--observe`), incr falls back to **try + strace**:

- **Write commands**: Run inside a **try** overlayfs sandbox. The command executes in an isolated overlay; strace records file access; try commit applies changes to the real filesystem. Requires `mergerfs` (or `unionfs`) and `try.sh`.
- **Read-only commands**: Use **strace** to trace file reads (TraceFile mode). No sandbox.
- **Pure commands**: No tracing (Nothing mode).

This fallback works without the observe project. It is slower for write commands (~250 ms cold vs ~23 ms with observe) but provides full isolation via the try overlay. Use it when observe is unavailable or when you need the sandbox’s stronger isolation guarantees.

---

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
