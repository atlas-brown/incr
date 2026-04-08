# Artifact Evaluation Guide — incr

This document explains how to run the `incr` benchmark suite end-to-end. All scripts are in `evaluation/benchmarks/`.

---

## What is incr?

`incr` automatically accelerates incremental execution of shell scripts. It traces a script's file dependencies on the first run and caches its outputs. On subsequent runs, if the inputs haven't changed, it replays outputs from cache instead of re-executing. The benchmark suite measures the speedup `incr` achieves over plain `bash` across 12 real-world workloads.

---

## Prerequisites

- Linux (tested on Ubuntu 20.04+)
- `bash`, `git`, `python3`, `sudo` (for apt installs in setup scripts)
- The `incr` binary must be built: `cargo build --release` from the repo root
- `ptrace_scope` must be 0 or 1 for `strace` to work:
  ```sh
  echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
  ```
- The **spell** benchmark’s `setup.sh` installs the `wamerican` package if `/usr/share/dict/words` is missing (scripts 6–7 use `comm` against that dictionary).

---

## Quick Start

### Option A — Validate with tiny inputs (fast, ~1 minute)

`run_all.sh` defaults to **`--mode easy`** and **`--size min`**, so you can run:

```sh
cd evaluation/benchmarks
bash run_all.sh
python3 show_results.py --size min
```

Equivalently: `bash run_all.sh --mode easy --size min`. This fetches minimal inputs, runs all 12 easy benchmarks under both `bash` and `incr`, and you can print a results table. No GPU, no API keys required.

### Option B — Standard evaluation with small inputs

```sh
cd evaluation/benchmarks
bash run_all.sh --mode easy --size small
python3 show_results.py --size small
```

**Wall time (12 easy benchmarks, both bash and incr):** typically **about 1–2 hours** on a machine with fast local disk and adequate free space; allow **2–4 hours** if I/O is slow or the host is heavily loaded. Per-benchmark timeout defaults to **4 hours** (`--timeout=SECS` to override).

For `--size small`, stdout capture files are **removed after each benchmark by default** (they can exceed 20 GB total). Timing CSVs still go to `run_results/small/`. To **diff bash vs incr stdout** for correctness, keep outputs and run `verify_outputs.sh` (see [Verifying bash vs incr outputs](#verifying-bash-vs-incr-outputs)):

```sh
bash run_all.sh --mode easy --size small --no-clear-outputs
bash verify_outputs.sh --size small
```

Reserve at least **30 GB free disk** if you use `--no-clear-outputs` (inputs plus retained `.out` files).

### Option C — Full evaluation including complex benchmarks

```sh
# dpt requires: pip install torch segment-anything, plus model download
# image-annotation requires: OPENAI_API_KEY set, llm CLI installed
cd evaluation/benchmarks
bash run_all.sh --mode full --size small
python3 show_results.py --size small
```

---

## Resource and time estimates (easy mode, 12 benchmarks)

Figures are approximate; **beginner** `--size small` input preparation alone needs **~32 GiB** free on the filesystem (see [Disk Space](#disk-space)).

| | **min** | **small** |
|---|---------|-----------|
| **Input data on disk (after setup)** | Under ~100 MB | Roughly **8–35 GB** (largest share is beginner nginx logs; other benchmarks add fetched data under each `inputs/`) |
| **Peak stdout/stderr under `outputs/<size>/`** | Under ~100 MB | Up to **~25 GB** if all benchmarks retain `.out` files (`--no-clear-outputs`) |
| **incr cache (per benchmark, cleared by default after each)** | Under ~100 MB each | Often **~0.5–3 GB** per benchmark while a run is active; default `--clear-cache` deletes it after each benchmark |
| **Wall clock (full `run_all.sh --mode easy`)** | **~5–20 minutes** (setup + run; network for first-time fetches adds variance) | **~1–2 hours** typical; **2–4 hours** on slower storage |

Timing-only runs (default: **clear outputs** after each benchmark for `--size small`) need less spare disk for stdout than the “verify outputs” workflow.

---

## run_all.sh — Global Orchestrator

```
Usage: bash run_all.sh [options]

Options:
  --mode easy|full       easy (default): 12 benchmarks, no special deps
                         full: all 14 benchmarks (needs GPU model + OpenAI key)
  --size min|small       min (default): tiny inputs, fast validation
                         small: evaluation-sized inputs
  --run-mode bash|incr|both
                         which modes to time (default: both)
  --only=a,b,c           run only these benchmark directories (comma-separated), e.g. spell,beginner
  --skip-setup           skip install/fetch phase (data must already be present)
  --clear-cache          clear incr cache after each benchmark (default: on)
  --no-clear-cache       keep caches
  --clear-outputs        delete stdout/stderr files after each benchmark
  --no-clear-outputs     keep those files (default for --size small is to clear them)
  --timeout=SECS         per-benchmark timeout, default 14400 (4 hours)
  --results-dir=DIR      where to write aggregated results (default: ../run_results)
  --help                 print help
```

The script runs two phases:

1. **Setup phase** — calls each benchmark's `setup.sh` to install system deps and fetch inputs. Idempotent: re-running skips already-downloaded data.
2. **Execution phase** — calls each benchmark's `run.sh` to time it under `bash`, `incr`, or both. Results go to `run_results/<size>/`.

If any benchmark's setup fails, that benchmark is skipped (the rest continue). Per-benchmark failures are reported in the final summary but do not abort the run.

---

## show_results.py — Print timing tables

Summarizes **`run_all.sh`** results from copied timing CSVs under `evaluation/run_results/<size>/`.

**Usage (from `evaluation/benchmarks/`):**

```text
python3 show_results.py [--size min|small] [--results-dir DIR] [--detail] [--help]
```

| Option | Meaning |
|--------|---------|
| `--size min` or `--size small` | Which subdirectory of `run_results/` to read (default: pick the most recent size that has data) |
| `--results-dir DIR` | Override results root (default: `../run_results` relative to `evaluation/benchmarks/`) |
| `--detail` | Print per-script times per benchmark, not only aggregate bash/incr seconds |
| `--help` / `-h` | Short usage |

**Example:**

```sh
cd evaluation/benchmarks
python3 show_results.py --size small
python3 show_results.py --size min --detail
```

Sample aggregate table:

```
┌──────────────────┬────────────┬────────────┬────────────┐
│Benchmark         │    bash (s)│    incr (s)│       cache│
├──────────────────┼────────────┼────────────┼────────────┤
│word-freq         │        5.51│        2.49│       38 MB│
│...               │         ...│         ...│         ...│
└──────────────────┴────────────┴────────────┴────────────┘
```

The table **sums** per-script times from one run. Incr often speeds up on later scripts in the same benchmark as the cache warms up.

### Compare to `evaluation/default_results/default_3`

```sh
cd evaluation/benchmarks
python3 compare_to_baseline.py
```

Prints current/baseline time ratios. Very small ratios on workloads that should take minutes usually mean missing inputs or a failed step.

---

## Verifying bash vs incr outputs

`verify_outputs.sh` **diffs** paired `*.bash.out` and `*.incr.out` under each benchmark’s `outputs/<size>/` directory. It also flags **empty** outputs and **“No space left on device”** lines in `*.err`.

**Requirements:** you must run benchmarks with **`--run-mode both`** (the default) so both stdout files exist, and you must **keep** output files on disk. For `--size small`, the default is to delete `outputs/` after each benchmark—use **`--no-clear-outputs`** on `run_all.sh` first.

**Usage (from `evaluation/benchmarks/`):**

```text
bash verify_outputs.sh [--size min|small|full] [--mode easy|full]
```

| Option | Meaning |
|--------|---------|
| `--size` | Which `outputs/<size>/` tree to check (default: `small`) |
| `--mode easy` or `--mode full` | Which benchmarks to scan (default: `easy` = 12 workloads; `full` includes `dpt` and `image-annotation`) |

**Examples:**

```sh
cd evaluation/benchmarks
# After: bash run_all.sh --mode easy --size min --no-clear-outputs
bash verify_outputs.sh --size min

# After a small run with outputs retained
bash run_all.sh --mode easy --size small --no-clear-outputs
bash verify_outputs.sh --size small
```

Exit code **0** means every paired file matched and no disk-full errors were found in stderr logs; **non-zero** means mismatches, skips, or errors (see script output).

**Correctness status:** the suite is intended to produce **identical stdout** for bash vs incr on these workloads. Run `verify_outputs.sh` after a full run with outputs retained to confirm on your machine. If `outputs/<size>/` is missing (e.g. outputs were cleared), the script exits with a message that nothing was checked.

---

## Running a Single Benchmark

Each benchmark has its own `setup.sh` and `run.sh`:

```sh
# Install deps and fetch inputs
bash evaluation/benchmarks/covid/setup.sh --min

# Time under bash, incr, or both
bash evaluation/benchmarks/covid/run.sh --mode both --size min
```

`run.sh` options:
- `--mode bash|incr|both` — which executor to use (default: both)
- `--size min|small|full` — which input size (default: small)
- `--scripts=a.sh,b.sh` — run only these script basenames under `scripts/` (omit for the full script list). Use this to debug or smoke-test one pipeline step without editing the benchmark.

For suite-level subsets (whole benchmarks, not individual scripts), use `run_all.sh --only=spell,beginner` instead of hand-invoking multiple `run.sh` commands.

Outputs go to `evaluation/benchmarks/<name>/outputs/<size>/`:
- `<script>.bash.out` / `<script>.incr.out` — stdout from each run
- `<script>.bash.err` / `<script>.incr.err` — stderr
- `timing.csv` — `mode,script,time_sec` rows

---

## Benchmark List

| Benchmark       | Description                              | Easy mode |
|-----------------|------------------------------------------|-----------|
| beginner        | Nginx log analysis (simple)              | yes       |
| bio             | Genomics pipeline (minimap2, samtools)   | yes       |
| covid           | COVID-19 time-series processing          | yes       |
| file-mod        | Audio conversion + encryption (ffmpeg)   | yes       |
| nginx-analysis  | Nginx log analytics (22 scripts)         | yes       |
| nlp-ngrams      | N-gram extraction from text              | yes       |
| nlp-uppercase   | Text normalization                       | yes       |
| poet            | Poetic analysis of text                  | yes       |
| spell           | Spell-checking pipeline                  | yes       |
| unixfun         | Chess data processing                    | yes       |
| weather         | Temperature analytics                    | yes       |
| word-freq       | Word frequency + set operations          | yes       |
| dpt             | Depth estimation (requires PyTorch+SAM)  | no        |
| image-annotation| LLM image annotation (requires OpenAI)   | no        |

---

## Robustness

All scripts are designed to be safe to kill and re-run:

- **`incr.sh`**: uses a sentinel file (`.incr_orig` next to the script) to survive SIGKILL. If killed mid-run, the original script is restored automatically on the next invocation.
- **`run.sh`** (each benchmark): has a `trap` on EXIT/INT/TERM that restores any sentinel files and removes stale OverlayFS mounts.
- **`run_all.sh`**: has a global `trap` on INT/TERM that restores sentinels across all benchmarks and cleans `/tmp` artifacts.
- **`setup.sh`** (each benchmark): idempotent — skips steps whose outputs already exist, so it is safe to re-run after a partial failure or interrupted download.

If anything gets stuck, it is safe to Ctrl+C and re-run from the beginning. The setup phase will skip already-downloaded data; the run phase will re-time from scratch.

---

## Disk Space

| Size  | Approx input data | Output files (stdout)  | Cache (cleared by default) |
|-------|-------------------|------------------------|----------------------------|
| min   | < 100 MB          | < 100 MB               | < 100 MB                   |
| small | ~8 GB             | up to ~25 GB           | ~500 MB                    |

**Important:** several benchmarks (especially `beginner`, `spell`) produce very large stdout output when run with small inputs because the scripts pipe large log files through `sort`. The `beginner` benchmark alone can produce ~19 GB of output files. Make sure you have at least **30 GB free** before running `--size small`.

**Beginner `--size small` inputs:** `beginner/fetch.sh` checks for **~32 GiB** free before download/merge; a partial `inputs/nginx-logs_small` after a failed run should be removed before retrying (`rm -rf evaluation/benchmarks/beginner/inputs/nginx-logs_small`).

Timing CSVs are always copied to `run_results/<size>/` before optional cache and output cleanup.

During benchmark runs, `run_lib.sh` sets `TMPDIR=/tmp` so `sort` and other tools use the system temp directory (consistent with `incr`’s expectations). After each timed script, `cleanup_tmp_artifacts` best-effort removes PaSh `try` and `sort` leftovers under `/tmp`.

With `--run-mode both`, **`run_lib.sh` runs bash and then incr for each script in turn** (not all bash scripts first, then all incr). Running all bash first used to fill the disk with huge stdout files before incr started; interleaving avoids that failure mode on `spell`, `unixfun`, `beginner`, etc.

After each timed script, **`cleanup_tmp_artifacts`** removes best-effort leftovers under `/tmp` (PaSh `try` sandboxes `*.try-*`, `sort` temp files `sort*` / `sort.*`). Intended for dedicated benchmark machines; do not rely on it if other users’ jobs use `/tmp/sort*`-named files.

**Maintainers:** do not commit `evaluation/run_results/` or other generated timing/output files until you have verified runs locally. Automated tooling may use a weaker model—treat generated artifacts as unreviewed by default.

---

## Troubleshooting

**`strace: attach: ptrace(PTRACE_SEIZE, ...): Operation not permitted`**
```sh
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

**`incr` hangs and never finishes**
The `incr` binary reads all of stdin as part of its cache key. In non-terminal environments, redirect stdin: `... < /dev/null`. The benchmark scripts do this automatically.

**A benchmark times out**
Increase the timeout: `bash run_all.sh --timeout=21600`. The default is 14400 seconds (4 hours); `beginner` at `--size small` can approach that limit.

**Benchmark outputs differ between bash and incr**
If stderr shows `No space left on device`, free disk space. Prefer the default (clear outputs after each benchmark when using `--size small`) or delete large `outputs/` trees between runs.

**Setup fails for one benchmark**
That benchmark is skipped; the rest continue. Check its `setup.sh` output in the terminal. You can re-run setup for just that benchmark: `bash evaluation/benchmarks/<name>/setup.sh --min`.

**`cargo build --release` not run yet**
The `incr` binary must exist at `target/release/incr`. Build it first:
```sh
cargo build --release
```
