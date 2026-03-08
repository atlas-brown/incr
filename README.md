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

When **observe** is built as a sibling project (`../observe/target/release/observe`), incr.sh automatically uses it for write commands, giving ~10x faster cold runs than the default strace/sandbox mode.

---

## Usage

### Script mode (recommended)

Transform and run a bash script so each command is executed incrementally:

```bash
./incr.sh <script> [cache_dir]
```

- **script**: Path to your bash script
- **cache_dir**: Optional; defaults to `/tmp/cache`
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
| strace + Sandbox | Full overlayfs isolation | ~250 ms | ~35 ms |
| **observe** | Direct execution + trace | **~23 ms** | **~18 ms** |

For write-heavy workloads, observe gives ~10x faster cold runs.

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
bash agent/test_incr_observe.sh

# Benchmark: strace vs observe
bash agent/run_bench.sh
python3 agent/benchmarks/plot.py agent/benchmarks/results.txt   # requires matplotlib
```

See `agent/README.md` for details.

---

## Benchmark (war-and-peace)

The `evaluation/war-and-peace` directory contains a basic benchmark. Run from the directory above `src`:

```bash
./evaluation/war-and-peace/with_cache.sh
./evaluation/war-and-peace/without_cache.sh
```

For Koala benchmarks, clone https://github.com/kbensh/koala and manually insert `target/release/incr` invocations into the benchmark scripts.
