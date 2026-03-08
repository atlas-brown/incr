# Evaluation Benchmark Suite

This doc explains how the **evaluation** benchmark suite works and how to install, run, and clean benchmarks in both **default** (try+strace) and **observe** modes. Use this when setting up a fresh VM to run the full suite.

> **Note**: This is distinct from `agent/benchmarks/` (microbenchmarks: strace vs observe). The evaluation suite lives in `evaluation/` and exercises real-world scripts.

---

## Overview

| Component | Path | Purpose |
|-----------|------|---------|
| Top-level runner | `evaluation/run.sh` | Entry point; delegates to benchmarks/run.sh |
| Benchmark runner | `evaluation/benchmarks/run.sh` | Runs all 14 benchmarks, sets mode |
| Per-benchmark | `evaluation/benchmarks/<name>/` | execute.sh, clean.sh, fetch.sh, install.sh, scripts/, inputs/ |
| Results | `evaluation/run_results/default/`, `evaluation/run_results/observe/` | timing CSVs and cache sizes |
| War-and-peace | `evaluation/war-and-peace/` | Standalone pipeline (cat\|tr\|sort\|uniq) |

---

## Modes

| Mode | Env | Tracing | Speed |
|------|-----|---------|-------|
| **default** | `INCR_OBSERVE=0` | try + strace (fallback) | Slower for write-heavy commands |
| **observe** | `INCR_OBSERVE=1` or unset | observe binary when available | ~10x faster for writes |

`incr.sh` reads `INCR_OBSERVE` and, when observe mode is enabled, uses `../observe/target/release/observe` if it exists and is executable. The benchmark runner exports this before each benchmark.

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

### Full suite (14 benchmarks)

```bash
# Both modes (default then observe)
bash evaluation/run.sh

# Single mode
bash evaluation/run.sh default   # try+strace only
bash evaluation/run.sh observe  # observe only
```

Results:

- `evaluation/run_results/default/<benchmark>-time.csv`
- `evaluation/run_results/observe/<benchmark>-time.csv`
- `evaluation/run_results/<mode>/<benchmark>-size.txt` (cache size in bytes)

### Single benchmark (e.g. weather)

```bash
# Default mode
INCR_OBSERVE=0 bash evaluation/benchmarks/weather/execute.sh --min

# Observe mode
INCR_OBSERVE=1 bash evaluation/benchmarks/weather/execute.sh --min
```

### War-and-peace (standalone pipeline)

Uses the incr binary directly (not incr.sh):

```bash
# Default (try+strace)
bash evaluation/war-and-peace/with_cache.sh

# Observe
bash evaluation/war-and-peace/with_cache_observe.sh

# Baseline (no incr)
bash evaluation/war-and-peace/without_cache.sh
```

Requires `evaluation/war-and-peace/book-large.txt` (or similar).

---

## Clean

### Per-benchmark clean

Each benchmark has `clean.sh` that removes `cache`, `outputs`, `plots`:

```bash
cd incr
sudo bash evaluation/benchmarks/weather/clean.sh
```

The full `run.sh` runs `sudo bash "./$benchmark/clean.sh"` before each benchmark.

### Full cleanup

```bash
cd incr

# Clean all benchmarks
for d in evaluation/benchmarks/*/; do
  [ -f "${d}clean.sh" ] && sudo bash "${d}clean.sh"
done

# Clean microbenchmarks
for d in evaluation/microbenchmarks/*/; do
  [ -f "${d}clean.sh" ] && bash "${d}clean.sh"
done

# Remove results
rm -rf evaluation/run_results

# Clean /tmp
rm -rf /tmp/cache* /tmp/sort* /tmp/tmp*
```

---

## Benchmark list (run.sh)

| # | Benchmark | Size | Fetch | Install |
|---|-----------|------|-------|---------|
| 1 | beginner | small | yes | - |
| 2 | bio | small | yes | yes |
| 3 | covid | small | yes | - |
| 4 | dpt | small | yes | yes |
| 5 | file-mod | small | yes | yes |
| 6 | image-annotation | small | yes | yes |
| 7 | nginx-analysis | small | yes | - |
| 8 | nlp-uppercase | small | yes | - |
| 9 | nlp-ngrams | small | yes | - |
| 10 | poet | small | yes | - |
| 11 | spell | small | yes | - |
| 12 | unixfun | small | yes | - |
| 13 | weather | small | yes | - |
| 14 | word-freq | small | yes | - |

---

## How it works

1. **run.sh** sets `INCR_OBSERVE` (0 or 1) and loops over benchmarks.
2. For each benchmark: `sudo clean.sh` → `execute.sh --small` → copy `timing.csv` and cache size → clean again.
3. **execute.sh** runs each script twice: once with `bash` (baseline), once with `incr.sh <script> <cache_dir>`.
4. **incr.sh** calls `insert.py` to transform the script (wrap commands with incr), then runs it. `insert.py` gets `--try-path`, `--cache-path`, and optionally `--observe-path`.
5. The transformed script invokes `incr -t <try> -c <cache> [--observe <observe>] -- <cmd> ...`. When `INCR_OBSERVE=1` and observe exists, incr.sh passes `--observe-path` to insert.py so the inserted incr calls use observe.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `du: cannot access './X/cache'` | Normal if a benchmark didn't create cache. run.sh writes `0` in that case. |
| `insert.py: unrecognized arguments` | incr.sh must use `--try-path` and `--cache-path` (not `--try`/`--cache`). |
| Observe not used | Ensure `observe/target/release/observe` exists and is executable. |
| Fetch fails (wget, network) | Use `--min` for weather; other benchmarks may need network. |
| install.sh fails | Install system deps (apt, pip) as needed; some benchmarks (file-mod, image-annotation) need Ollama/LLM. |

---

## Quick VM setup checklist

```bash
# 1. Clone and build
cd atlas/incr && cargo build --release
cd ../observe && cargo build --release

# 2. Fetch all benchmark inputs
cd incr
for b in evaluation/benchmarks/*/; do [ -f "${b}fetch.sh" ] && bash "${b}fetch.sh" --small; done

# 3. Install deps for bio, dpt (and file-mod, image-annotation if desired)
bash evaluation/benchmarks/bio/install.sh
bash evaluation/benchmarks/dpt/install.sh

# 4. Run full suite (both modes)
bash evaluation/run.sh

# 5. Results
ls evaluation/run_results/default/
ls evaluation/run_results/observe/
```
