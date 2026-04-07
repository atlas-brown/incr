# incr

Bolt-on incremental execution for the shell. Incr wraps shell commands to track their file dependencies and memoize their results, so that unchanged commands are skipped on re-execution and their outputs are replayed from cache.

## Setup

1. Ensure Ubuntu 22.04 is running with updated packages:
```sh
sudo apt update && sudo apt upgrade
```
2. Install system dependencies (OverlayFS, strace, pip):
```sh
sudo apt install mergerfs strace python3-pip
```
3. Install Rust via rustup:
```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
4. Install Python dependencies for the `insert.py` script:
```sh
pip3 install --no-cache-dir -r requirements.txt
```
5. Build the binary:
```sh
cargo build --release
```

See [FUNCTIONAL.md](./FUNCTIONAL.md) for a minimal walkthrough and [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full evaluation instructions.

### Docker

```sh
docker build -t incr .
docker run -it --rm -v $(pwd):/app --privileged incr
```

Toggle `DEBUG` and `DEBUG_LOGS` in `src/config.rs` for debug output.

## Architecture

`incr` intercepts shell command execution to memoize results. On re-execution, it replays cached stdout/stderr and file outputs when the command's inputs, environment, and file dependencies are unchanged, using strace and an OverlayFS sandbox to track side effects.

- **`src/main.rs`** - CLI entrypoint that selects an execution strategy for each command.
- **`src/command.rs`** - Represents a command invocation and handles spawning child processes.
- **`src/execution/`** - Execution engines that manage tracing, caching, and replaying command results.
- **`src/cache/`** - Stores and retrieves memoized outputs and file dependency information.
- **`src/config.rs`** - Runtime and compile-time configuration constants.
- **`src/scripts/`** - Helper scripts for parsing trace output and rewriting shell scripts to use incr.

## Quick Start

The `evaluation/war-and-peace` pipeline counts word frequencies. `without_incr.sh` runs it under plain Bash; `with_incr.sh` wraps each command with `incr`:

```sh
bash ./evaluation/war-and-peace/without_incr.sh > baseline.txt
bash ./evaluation/war-and-peace/with_incr.sh > incr.txt
diff baseline.txt incr.txt
```

The first run is a cold start (tracing overhead). Run `with_incr.sh` again to see cached replay. Clean up with `bash ./evaluation/war-and-peace/clean.sh`.

## Benchmarks

Each of 14 scenarios in `evaluation/benchmarks/` has an `execute.sh` that times the script under both Bash and `incr.sh`. The top-level driver runs all of them:

```sh
cd evaluation/benchmarks && bash ./run.sh
```

Results go to `evaluation/run_results/`. Speedup is `bash_time / incr_time` on re-executions after the cold run.

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full benchmark setup and the behavioral-equivalence harness.
