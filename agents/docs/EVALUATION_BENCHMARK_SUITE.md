# Evaluation Benchmark Suite

This doc explains how the **evaluation** benchmark suite works: `run_all.sh` orchestrates the same layout as `incr/main/benchmarks/` for mergeability. Use it when setting up a fresh VM.

> **Note**: Distinct from `agents/benchmarks/` (microbenchmarks: strace vs observe). The evaluation suite lives in `evaluation/` and exercises real-world scripts.

---

## Overview

| Component | Path | Purpose |
|-----------|------|---------|
| Orchestrator | `evaluation/benchmarks/run_all.sh` | Setup phase + runs each benchmark’s `run.sh` |
| Thin wrapper | `evaluation/run.sh` | Forwards args to `run_all.sh` |
| Shared library | `evaluation/benchmarks/run_lib.sh` | Timing, `restore_instrumented_scripts`, cleanup |
| Per-benchmark | `evaluation/benchmarks/<name>/` | `run.sh`, `setup.sh`, `execute.sh`, `fetch.sh`, `scripts/`, `inputs/` |
| Results | `evaluation/run_results/<min\|small>/` | Copied `*-time.csv`, `*-size.txt` |
| War-and-peace | `evaluation/war-and-peace/` | Standalone pipeline |

---

## Modes (`--run-mode` for `run_all.sh` / per-benchmark `run.sh`)

| Mode | Meaning |
|------|--------|
| `bash` | Baseline only |
| `incr` | `INCR_OBSERVE=0` — try + strace (no observe) |
| `incr-observe` | `INCR_OBSERVE=1` — observe when `../observe/target/release/observe` exists |
| `both` | bash + incr |
| `all` | bash + incr + incr-observe (full comparison) |

`incr.sh` sets `OBSERVE_PATH` when `INCR_OBSERVE` is not `0` and the observe binary exists.

---

## Prerequisites

### Repo layout

```
atlas/
├── incr/           # main repo
│   ├── incr.sh
│   ├── target/release/incr
│   ├── src/scripts/try.sh
│   ├── src/scripts/insert.py
│   └── evaluation/
└── observe/        # sibling to incr
    └── target/release/observe
```

### Build

```bash
cd incr && cargo build --release
cd ../observe && cargo build --release
```

### Python dependencies (required for incr.sh)

incr.sh uses `insert.py` which requires libbash, libdash, shasta. Install with:

```bash
pip install --user libbash libdash shasta
# Or: pip install -r incr/requirements.txt
```

Without these, benchmarks may complete in seconds (incorrect) instead of ~1 hour.

### Permissions

- `run.sh` uses `sudo` for `clean.sh`. Ensure the agent has sudo access.
- Some benchmarks (bio, dpt, file-mod, image-annotation, web-search) have `install.sh` that use `sudo apt-get` and `pip`.

---

## Install (per benchmark)

Before running, **fetch** inputs and **install** dependencies where needed.

### Fetch inputs (all benchmarks)

Each benchmark has `fetch.sh` that downloads or generates inputs. The runner uses `--small` for most benchmarks. Some support `--min` (local data only) or `--full`.

```bash
cd incr

# Fetch all benchmarks at small size (matches run.sh)
for b in evaluation/benchmarks/*/; do
  [ -f "${b}fetch.sh" ] && bash "${b}fetch.sh" --small
done
```

For a quick smoke test, use `--min` where available (e.g. weather):

```bash
bash evaluation/benchmarks/weather/fetch.sh --min
```

### Install dependencies (selected benchmarks)

These benchmarks have non-empty `install.sh`:

| Benchmark | Dependencies |
|-----------|--------------|
| bio | apt packages |
| dpt | apt, pip (numpy, etc.) |
| file-mod | apt, pip (llm, llm-ollama, etc.) |
| image-annotation | apt, pip (llm, etc.) |
| web-search | apt, node, npm, pandoc |

```bash
cd incr

# Install for benchmarks that need it
bash evaluation/benchmarks/bio/install.sh
bash evaluation/benchmarks/dpt/install.sh
# file-mod, image-annotation, web-search if you need them
```

`web-search` is **not** in the default benchmark list in `run.sh`; it may require Docker or extra setup.

---

## Run

All commands from `incr/`.

### EASY benchmarks (recommended first run)

```bash
# All three modes: bash + incr + incr-observe (min inputs)
bash evaluation/run.sh --mode easy --size min --run-mode all

# Faster: just bash + incr
bash evaluation/run.sh --mode easy --size min --run-mode both
```

Results: `evaluation/run_results/min/<benchmark>-time.csv`.

### Full suite (14 benchmarks, paper-sized inputs)

```bash
bash evaluation/run.sh --mode full --size small --run-mode all
```

Results: `evaluation/run_results/small/<benchmark>-time.csv`.

### Single benchmark

```bash
# Run weather with all modes at min size
bash evaluation/benchmarks/run_all.sh --only weather --size min --run-mode all

# Or directly via per-benchmark run.sh
bash evaluation/benchmarks/weather/run.sh --mode=all --size=min
```

### Run modes

```bash
bash evaluation/run.sh --run-mode bash          # baseline only
bash evaluation/run.sh --run-mode incr          # try+strace (INCR_OBSERVE=0)
bash evaluation/run.sh --run-mode incr-observe  # observe (INCR_OBSERVE=1)
bash evaluation/run.sh --run-mode both          # bash + incr
bash evaluation/run.sh --run-mode all           # bash + incr + incr-observe
```

---

## Clean

### Restore instrumented scripts (run after any interrupted benchmark)

```bash
cd incr
bash evaluation/scripts/restore_sentinels.sh
```

### Full artifact cleanup

```bash
cd incr

# Remove caches, outputs for all benchmarks
for d in evaluation/benchmarks/*/; do
  rm -rf "${d}cache" "${d}outputs"
done

# Remove timing results
rm -rf evaluation/run_results

# Clean /tmp artifacts
rm -rf /tmp/sort* /tmp/tmp* /tmp/incr_bench* /tmp/incr_cache
```

---

## Benchmark list

| # | Benchmark | Mode | Install? |
|---|-----------|------|----------|
| 1 | beginner | EASY | - |
| 2 | bio | EASY | yes (samtools, minimap2) |
| 3 | covid | EASY | - |
| 4 | file-mod | EASY | yes (ffmpeg) |
| 5 | nginx-analysis | EASY | - |
| 6 | nlp-ngrams | EASY | - |
| 7 | nlp-uppercase | EASY | - |
| 8 | poet | EASY | - |
| 9 | spell | EASY | - |
| 10 | unixfun | EASY | - |
| 11 | weather | EASY | - |
| 12 | word-freq | EASY | - |
| 13 | dpt | full only | yes (torch, segment-anything) |
| 14 | image-annotation | full only | yes (llm, OpenAI key) |

---

## How it works

1. `run_all.sh` (orchestrator) runs each benchmark's `setup.sh` (fetch + install), then calls `run.sh`.
2. Each `run.sh` sources `run_lib.sh` and calls `run_benchmark_scripts()` for each script.
3. For mode `incr`: `run_lib.sh` calls `INCR_OBSERVE=0 incr.sh <script> <cache_dir>`.
4. For mode `incr-observe`: `run_lib.sh` calls `INCR_OBSERVE=1 incr.sh <script> <cache_dir>`.
5. `incr.sh` calls `insert.py` to transform the script (wrapping commands with `incr`), then runs it. With `INCR_OBSERVE=1` and observe binary present, `--observe-path` is passed so observe-mode tracing is used instead of strace.
6. Results (`timing.csv`, cache size) are copied to `evaluation/run_results/<size>/`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Instrumented scripts left behind | `bash evaluation/scripts/restore_sentinels.sh` |
| `insert.py: unrecognized arguments` | Ensure incr.sh uses `--try-path` / `--cache-path` / `--observe-path` |
| Observe not used | Ensure `observe/target/release/observe` exists and is executable |
| Benchmark finishes in ~3s (wrong) | Missing Python deps: `pip install libbash libdash shasta` |
| Fetch fails (wget, network) | Use `--size min` for local inputs; other sizes need network |
| install.sh fails | Install system deps (apt, pip) as needed |

---

## Quick VM setup

```bash
# 1. Build
cd atlas/incr && cargo build --release
cd ../observe && cargo build --release

# 2. Python deps (required for incr.sh)
pip install --user libbash libdash shasta

# 3. Restore scripts (if prior interrupted run)
cd incr && bash evaluation/scripts/restore_sentinels.sh

# 4. Run EASY benchmarks (min inputs, fast)
bash evaluation/run.sh --mode easy --size min --run-mode all

# 5. Check results
ls evaluation/run_results/min/

# 6. Verify outputs match between incr and incr-observe
bash evaluation/scripts/verify_outputs.sh --min
```
