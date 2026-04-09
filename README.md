# incr

Bolt-on incremental execution for the shell. Incr wraps shell commands to track their file dependencies and memoize their results, so that unchanged commands are skipped on re-execution and their outputs are replayed from cache.

## Setup

The quickest path is Ubuntu 22.04 with the bootstrap script:

```sh
curl -fsSL https://raw.githubusercontent.com/atlas-brown/incr/main/scripts/up.sh | sh
cd ~/incr
```

The bootstrap script installs:

* Rust via `rustup` if needed
* Ubuntu packages: `git`, `mergerfs`, `strace`, `python3-pip`, `curl`, `ca-certificates`, `build-essential`, `pkg-config`, and `libssl-dev`
* Python dependencies from `requirements.txt`
* the release binary via `cargo build --release`

If you prefer to install manually on Ubuntu 22.04:

1. Update packages:
```sh
sudo apt update && sudo apt upgrade -y
```
2. Install system dependencies:
```sh
sudo apt install -y git mergerfs strace python3-pip curl ca-certificates build-essential pkg-config libssl-dev
```
3. Install Rust via `rustup`:
```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
4. Install Python dependencies:
```sh
pip3 install --no-cache-dir -r requirements.txt
```
5. Build the release binary:
```sh
cargo build --release
```

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full evaluation instructions.

### Docker

```sh
docker build -t incr .
docker run -it --rm --privileged incr
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

To sanity-check the install with a minimal example:

```sh
./incr.sh ./evaluation/hello-world.sh
```

This should print the same `Hello, world!`-style output as the underlying shell script, while exercising the `incr.sh` entrypoint.

The `evaluation/war-and-peace` pipeline counts word frequencies. Run the combined harness:

```sh
./evaluation/war-and-peace/test.sh
```

This runs:

1. the baseline Bash pipeline,
2. a cold Incr run, and
3. a warm Incr run that should reuse cached results.

It checks that both Incr outputs match the baseline. Clean up with `bash ./evaluation/war-and-peace/clean.sh`.

## Benchmarks

Each benchmark under `evaluation/benchmarks/` has its own setup and execution scripts. The main suite driver is `run_all.sh`:

```sh
cd evaluation/benchmarks && ./run_all.sh --mode=easy --size=min --run-mode=both
```

Results are written under `evaluation/run_results/`. Use `python3 ./show_results.py --size min` to print a summary, and `bash ./verify_outputs.sh --mode=easy --size=min` to check Bash/Incr output agreement.

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for full benchmark setup and the behavioral-equivalence harness.

## Citing Incr

If you use Incr or build on any component in this repository, please cite the following paper:

```bibtex
@inproceedings{incr:osdi:2026,
  title = {Incr: Faster Re-execution via Bolt-on Incrementalization},
  author = {Xie, Yizheng and Lamprou, Evangelos and Xia, Jerry and Vasilakis, Nikos},
  booktitle = {20th USENIX Symposium on Operating Systems Design and Implementation (OSDI 26)},
  year = {2026},
  publisher = {USENIX Association},
  tags = {performance}
}
```

## License & Contributing

Incr is an open-source, collaborative, [MIT-licensed](./LICENSE) project developed by the [ATLAS group](https://atlas.cs.brown.edu/) at [Brown University](https://cs.brown.edu/). If you'd like to contribute, please see [CONTRIBUTING.md](./CONTRIBUTING.md) — contributions, bug reports, and reproducibility feedback are welcome.
