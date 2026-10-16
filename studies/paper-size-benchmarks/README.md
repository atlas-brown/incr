# Maintained benchmark runner

This is the single supported three-mode benchmark harness: native Bash, original Incr at `4b8e5ddf8e275d947518c7cc0f5d2713fe992307` plus `reference/original-minimal-fixes.patch`, and current Incr with Observe. Annotations are off. Original baseline fixes and workload repairs are documented in [CHANGE_AUDIT.md](CHANGE_AUDIT.md); assumptions are in [EVALUATION_PROTOCOL.json](EVALUATION_PROTOCOL.json).

All saved historical/current measurements are in [the consolidated study](../evaluation-checkpoint-2026-10-16/README.md). The full reproduction was cancelled on request: twelve families complete, partial DPT, supplemental not started. No controllers or timers remain scheduled. This directory holds programs/methodology, not old measurements or caches.

## Prerequisites

Build both repositories with `cargo build --release --locked`. Keep the sibling Observe checkout. To recreate the comparison checkout when absent:

```bash
git worktree add --detach ../incr-main-qualification 4b8e5ddf8e275d947518c7cc0f5d2713fe992307
git -C ../incr-main-qualification apply "$PWD/studies/paper-size-benchmarks/reference/original-minimal-fixes.patch"
cargo build --release --locked --manifest-path ../incr-main-qualification/Cargo.toml
```

The Python environment is `qualification/.venv`; parser packages are libbash 0.1.14, libdash 0.5.2 and shasta 0.5. Minimum seeds are versioned under each workload's `min_inputs`; no old prepared-input tree is required. DPT requires the full real models even at minimum size: explicitly run `python3 studies/paper-size-benchmarks/harness/setup_models.py` to download and verify their recorded hashes. This download is outside timings and is never automatic. The retained environment has TensorFlow CPU, CPU PyTorch/torchvision, segment-anything, OpenCV and plotting packages; exact measured versions are in the consolidated environment records.

System tools include Bash, strace, mergerfs/FUSE, ffmpeg, OpenSSL, samtools, minimap2, gnuplot, ImageMagick, unzip, col, a C compiler and GNU time. Sandbox tests require noninteractive sudo. Supplemental web search needs Node 22.20.0 in `qualification/.tools/node-v22.20.0-linux-x64` and dependencies from its versioned package.json (`npm ci --ignore-scripts` in `evaluation/benchmarks/web-search/scripts`). Installed toolchains and the Python environment are prerequisites, not result snapshots.

## Explicit serial workflow

From the Incr root:

```bash
bash studies/paper-size-benchmarks/run.sh doctor
bash studies/paper-size-benchmarks/run.sh prepare --profile min
bash studies/paper-size-benchmarks/run.sh run --profile min --run-id min-check --repetitions 1 --native-transform --assume-directory-access --content-validated-inputs

# Only after correctness/performance qualification; choose a new ID.
bash studies/paper-size-benchmarks/run.sh prepare --profile paper
bash studies/paper-size-benchmarks/run.sh run --profile paper --run-id full-new --repetitions 3 --native-transform --assume-directory-access --content-validated-inputs --release-inputs
```

Use `--only family1,family2` to restrict an explicit stage. Historical scope is thirteen families/828 invocations at three paired repetitions. For web-search and weather-Tufte, set `INCR_BENCH_SUITE=supplemental` on each command and use `--profile full`: 45 invocations, separately reported. Only API-key image annotation is excluded. Never overlap timed workloads or substitute minimum datasets for full runs.

`harness/launch.py` explicitly launches one prepared run under systemd; inspect `--help` first. It does not chain a second cohort. `harness/monitor.py RUN` audits saved evidence; `harness/cohort_report.py RUN --output REPORT.json` requires complete paired cohorts. Use `harness/cleanup.py` to inspect/remove only owned disposable state. No launch occurs on import or preparation. Resource limits are 32 GiB workspace and 8 GiB disk reserve. Failed or incomplete measurements remain labelled and are never promoted to final aggregate statistics.
