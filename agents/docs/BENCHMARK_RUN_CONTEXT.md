# Benchmark Run Context & Best Practices

This document summarizes lessons learned from running the evaluation benchmark suite and provides detailed instructions for reliable, correct benchmark execution in new environments.

---

## Executive Summary

- **Primary entry point:** `bash evaluation/benchmarks/run_all.sh` (or `bash evaluation/run.sh`, same args). Results: `evaluation/run_results/<min|small>/`.
- **`--run-mode`:** `incr` = try+strace (`INCR_OBSERVE=0`); `incr-observe` = observe (`INCR_OBSERVE=1`); `all` = bash + incr + incr-observe per script. Compare `*.incr.out` vs `*.incr-observe.out` or use `evaluation/scripts/verify_outputs.sh`.
- **Always run `restore_benchmark_scripts.sh`** after a failed/interrupted run — incr uses sentinel files (`*.incr_orig`) and can leave scripts instrumented.
- **Setup:** `run_all.sh` runs each benchmark’s `setup.sh` (unless `--skip-setup`). bio/dpt need `install.sh` deps for full correctness.
- **Parallel:** `evaluation/scripts/run_parallel.sh` is optional (batches per-benchmark `run_all --only …`). Not the canonical path.
- **Heavy / optional:** `image-annotation` (API keys), `dpt` (long). EASY mode has 12 benchmarks including `file-mod` (min inputs generated via ffmpeg in `setup.sh`).

---

## 1. Prerequisites Checklist

### 1.1 Build

```bash
cd incr && cargo build --release
cd ../observe && cargo build --release
```

### 1.2 Python (for incr.sh insert.py)

```bash
pip install --user libbash libdash shasta
```

Without these, benchmarks finish in ~3 seconds instead of ~1 hour—incorrect.

### 1.3 Per-Benchmark Dependencies

| Benchmark | install.sh | Key deps | Verify |
|-----------|------------|----------|--------|
| bio | yes | samtools, minimap2, gnuplot | `which samtools` |
| dpt | yes | torch, torchvision, segment-anything, tensorflow, opencv, ImageMagick | `python3 -c "import torchvision; import segment_anything"` |
| file-mod | yes | ffmpeg, imagemagick | `which ffmpeg` |
| image-annotation | yes | llm, OpenAI key | (excluded from suite) |
| nginx-analysis, beginner, covid, etc. | no | standard tools | - |

**Run install before first benchmark:**

```bash
cd incr
bash evaluation/benchmarks/bio/install.sh
bash evaluation/benchmarks/dpt/install.sh
bash evaluation/benchmarks/file-mod/install.sh
```

### 1.4 Permissions

- `run_all.sh` / per-benchmark `run.sh` and `run_parallel.sh` use `sudo` for `clean.sh` where needed. Ensure sudo access.
- mergerfs (for try overlayfs) when using incr without observe: `sudo apt install mergerfs`

---

## 2. Fetch Inputs

```bash
cd incr

# Full fetch (matches run.sh --small)
for b in evaluation/benchmarks/*/; do
  [ -f "${b}fetch.sh" ] && bash "${b}fetch.sh" --small
done
```

**Excluded from run.sh**: image-annotation (OpenAI key), file-mod (no min_inputs; run manually with `--small`).

---

## 3. How to Run Benchmarks Correctly

### 3.1 Recommended: run_all.sh (Primary)

**Canonical command** (EASY, min inputs, all three modes):

```bash
cd incr
bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all
```

Results are written to `evaluation/run_results/min/`. Per-benchmark `outputs/min/` holds stdout/stderr and `.incr.out` / `.incr-observe.out` for comparison.

### 3.2 Optional: Parallel Runner (Heuristic)

**Parallel batches** (`run_parallel.sh`) call `run_all.sh --only <bench>` per benchmark. Results still land under each benchmark’s `outputs/` and `run_results/` when copied. Use for throughput, not as the only correctness check.

```bash
cd incr
bash evaluation/scripts/restore_benchmark_scripts.sh
# Optional parallel (logs only; copies timing via run_all internals)
bash evaluation/scripts/run_parallel.sh --min --run-mode both --skip-dpt
```

**Parallel runner:** logs under `evaluation/parallel_logs/<benchmark>.log`. Each job runs `run_all.sh --only <benchmark> …`.

### 3.3 Single benchmark or subset

```bash
cd incr
bash evaluation/benchmarks/run_all.sh --only covid --size min --run-mode all --skip-setup
# or per-benchmark:
bash evaluation/benchmarks/covid/run.sh --mode=both --size=min
```

### 3.4 Background Runs with Polling

Use `run_bench_background.sh` for unattended runs; it writes a timestamped log to `/tmp/`:

```bash
cd incr
bash evaluation/scripts/run_bench_background.sh --mode easy --size min --run-mode all
```

For manual background + polling:

```bash
# Start
nohup bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all \
  > /tmp/bench_run.log 2>&1 &
PID=$!
echo "Started PID: $PID"

# Poll every 60s
sleep 60
tail -20 /tmp/bench_run.log
ps -p $PID -o pid,etime || echo "Process ended"
```

---

## 4. Baseline & Error Checking

### 4.1 Results Format

Each run writes `evaluation/run_results/<size>/<benchmark>-time.csv` with per-script timings:

```csv
mode,script,time_sec
bash,wf.sh,5.2
incr,wf.sh,5.5
incr-observe,wf.sh,4.9
bash,top-n.sh,0.18
incr,top-n.sh,0.21
```

Cache sizes are in `<benchmark>-size.txt`.

### 4.2 Detecting Wrong Results

**Suspiciously short times indicate failure.** Examples:

| Benchmark | Script | Baseline (approx, small) | Suspicious |
|-----------|--------|--------------------------|------------|
| word-freq | wf.sh | ~5.5s | <1s (empty output) |
| word-freq | top-n.sh | ~0.2s | ~0.1s (if wf.sh failed) |
| bio | bio-1.sh | ~7–50s | <1s |
| dpt | dpt_1.sh | ~194s | <5s |

If a script's time is **much shorter** than expected (e.g. 10x+), the run likely failed.

### 4.3 How to Check for Errors

1. **Inspect the timing CSV** after a run:
   ```bash
   cat evaluation/run_results/min/word-freq-time.csv
   # incr,wf.sh should be >1s with min inputs; <0.1s means pipeline failed
   ```

2. **Check output file sizes**:
   ```bash
   wc -l evaluation/benchmarks/word-freq/outputs/wf.sh.incr.out
   # Expect: 10285 lines for word-freq. If 0, the run failed.
   ```

3. **Check stderr** for failures:
   ```bash
   tail -50 evaluation/benchmarks/<name>/outputs/<script>.incr.err
   # Look for: ENOENT, ModuleNotFoundError, "command not found"
   ```

4. **Run verify_outputs.sh** to ensure default and observe produce identical outputs:
   ```bash
   bash evaluation/scripts/verify_outputs.sh
   ```

### 4.4 Common Failure Causes

- **Empty scripts**: Incr overwrites scripts in place. If interrupted, scripts can be left empty. Run `restore_benchmark_scripts.sh`.
- **word-freq <1s**: Usually means wf.sh or top-n.sh was empty, or resource contention when too many benchmarks ran at once. Restore scripts and use run_parallel (which runs word-freq first).
- **Missing Python deps**: Benchmarks finish in seconds. `pip install libbash libdash shasta`.
- **Missing benchmark deps**: bio (samtools), dpt (torchvision), file-mod (ffmpeg). Run install.sh.

---

## 5. Output Validation

### 5.1 Check for Empty Outputs

Many benchmarks write to `outputs/`. Empty files indicate pipeline failure:

```bash
# word-freq: wf.sh.incr.out should have ~10k lines
wc -l evaluation/benchmarks/word-freq/outputs/wf.sh.incr.out

# dpt: db.incr.txt should have lines (e.g. "g: A13 c: 0.30...")
wc -l evaluation/benchmarks/dpt/outputs/db.incr.txt

# file-mod: outputs should have .wav or .tar files
ls evaluation/benchmarks/file-mod/outputs/
```

### 5.2 Check stderr for Failures

```bash
tail -50 evaluation/benchmarks/<name>/outputs/<script>.incr.err
```

Common patterns:

- `ffmpeg: ENOENT` → install ffmpeg
- `samtools: command not found` → run bio/install.sh
- `ModuleNotFoundError: No module named 'torchvision'` → `pip install torchvision`
- `mogrify: command not found` → `apt install imagemagick`

### 5.3 verify_outputs.sh

Verifies that default and observe produce identical outputs:

```bash
cd incr
bash evaluation/scripts/verify_outputs.sh --min      # faster, uses --min
bash evaluation/scripts/verify_outputs.sh           # uses --small
bash evaluation/scripts/verify_outputs.sh --no-cleanup  # keep artifacts for inspection
```

---

## 6. Restore Benchmark Scripts

Incr overwrites benchmark scripts in place. If a run is interrupted (kill, Ctrl+C), scripts can be left empty or instrumented. **Always run restore before benchmarking:**

```bash
cd incr
bash evaluation/scripts/restore_benchmark_scripts.sh
```

This script:
- Restores scripts with incr instrumentation (git checkout)
- Restores empty `.sh` files (e.g. word-freq wf.sh, top-n.sh)
- Removes stray `incr_script_*` temp files

---

## 7. Benchmark-Specific Notes

### 7.1 word-freq

- **Critical**: Runs first in run_parallel (fails when run alongside many others due to resource contention)
- **Output**: wf.sh.incr.out should have ~10,285 lines
- **Baseline**: wf.sh ~5.5s, top-n.sh ~0.2s

### 7.2 bio

- **Deps**: samtools, minimap2, gnuplot (via install.sh)
- **Verify**: `which samtools`
- **Typical speedup**: observe ~2x faster

### 7.3 dpt

- **Deps**: torch, torchvision, segment-anything, tensorflow, opencv, ImageMagick
- **Output**: `outputs/db.incr.txt` should have lines like `g: A13 c: 0.30...`
- **Cache**: default gets cache hits for dpt_3a, dpt_3b, dpt_5a–e. Observe may not on some machines.
- **Typical**: default ~591s (with cache), observe ~979s (no cache)

### 7.4 file-mod

- **Deps**: ffmpeg (via install.sh)
- **Excluded** from run.sh (no min_inputs). Run manually with `--small`.
- **Verify**: `which ffmpeg`

### 7.5 nginx-analysis, beginner, covid, etc.

- Use standard tools (grep, awk, sort). No install.sh.
- Usually similar or slightly faster with observe.

---

## 8. Modes: Default vs Observe

| Mode | INCR_OBSERVE | Tracing | When faster |
|------|--------------|---------|-------------|
| default | 0 | try + strace (sandbox) | dpt (cache hits), some read-heavy |
| observe | 1 | observe (ptrace, no sandbox) | bio, file-mod, nlp-ngrams (write-heavy) |

**Observe** runs commands directly (no overlayfs). **Default** uses try overlayfs + strace. Cache keys are the same; cache validity can differ because observe may trace more paths (e.g. /tmp) that change between runs.

---

## 9. Results & Plots

Results are in `evaluation/run_results/<size>/`. After a run with `--run-mode all`:

```bash
cd incr/evaluation/analysis
python3 compare_default_observe.py --results-dir ../run_results/min --skip-dpt
```

Outputs: `plots/default_vs_observe.pdf`, `.png`

The script reads per-benchmark `*-time.csv` files and compares `incr` vs `incr-observe` totals.

---

## 10. Parallel Runner & Monitoring

### 10.1 run_parallel.sh

```bash
cd incr
bash evaluation/scripts/run_parallel.sh              # all benchmarks including dpt
bash evaluation/scripts/run_parallel.sh --skip-dpt   # skip dpt (longest, ~10+ min)
```

- Runs in batches of 3
- word-freq first (avoids resource contention)
- Cleans caches between batches
- Cleans up on exit

### 10.2 monitor_benchmarks.sh

```bash
bash evaluation/scripts/monitor_benchmarks.sh           # one-shot status
bash evaluation/scripts/monitor_benchmarks.sh --loop    # refresh every 60s
```

### 10.3 Plotting

```bash
cd incr/evaluation/analysis
python3 compare_default_observe.py --results-dir ../run_results/min --skip-dpt
```

---

## 11. Observe-Mode Optimization

**OBSERVE_READ_EXCLUDED_PATHS** (in `incr/src/config.rs`): filters `/tmp`, `/dev`, `/proc`, `/sys` from observe-mode read dependencies at parse time. Improves cache hits for observe (e.g. nlp-ngrams, bio).

---

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| word-freq <1s, empty output | Empty scripts or resource contention | `restore_benchmark_scripts.sh`; use run_parallel (word-freq first) |
| Benchmark finishes in seconds | Missing Python deps (libbash, libdash, shasta) | `pip install libbash libdash shasta` |
| file-mod ~12s total | ffmpeg not installed | `apt install ffmpeg` or run file-mod/install.sh |
| bio fails immediately | samtools not installed | `bash benchmarks/bio/install.sh` |
| dpt db.incr.txt empty | torchvision or segment_anything missing | `pip install torchvision segment-anything` |
| observe much slower than default (dpt) | Observe not getting cache hits | Expected on some machines |
| Command timeout / hang | Long-running benchmark | Use background + polling |

---

## 13. Quick Setup for New Machine

```bash
# 1. Build
cd atlas/incr && cargo build --release
cd ../observe && cargo build --release

# 2. Python deps (required for incr.sh)
pip install --user libbash libdash shasta

# 3. Restore scripts (in case of prior interrupted runs)
cd incr
bash evaluation/scripts/restore_benchmark_scripts.sh

# 4. Run EASY benchmarks at min size (fast smoke test)
bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all

# 5. Check results
cat evaluation/run_results/min/word-freq-time.csv

# 6. Verify outputs match between incr and incr-observe
bash evaluation/scripts/verify_outputs.sh --min

# 7. For paper-sized workloads, install deps and fetch inputs first
bash evaluation/benchmarks/bio/install.sh
bash evaluation/benchmarks/dpt/install.sh
bash evaluation/benchmarks/file-mod/install.sh
for b in evaluation/benchmarks/*/; do
  [ -f "${b}fetch.sh" ] && bash "${b}fetch.sh" --small
done

# 8. Run full suite
bash evaluation/benchmarks/run_all.sh --mode easy --size small --run-mode all
```

---

## 14. Artifact Cleanup

```bash
cd incr

# Restore any instrumented benchmark scripts first
bash evaluation/scripts/restore_benchmark_scripts.sh

# Remove caches and outputs for all benchmarks
for d in evaluation/benchmarks/*/; do
  rm -rf "${d}cache" "${d}outputs"
done

# Remove results and logs
rm -rf evaluation/run_results evaluation/parallel_logs

# /tmp artifacts
rm -rf /tmp/sort* /tmp/tmp* /tmp/incr_bench* /tmp/incr_cache
```

---

## 15. Files Reference

| Path | Purpose |
|------|---------|
| `evaluation/benchmarks/run_all.sh` | **Primary** orchestrator; setup + run all/subset benchmarks |
| `evaluation/run.sh` | Thin wrapper forwarding args to `run_all.sh` |
| `evaluation/benchmarks/run_lib.sh` | Shared helpers: `measure()`, `restore_instrumented_scripts`, cleanup |
| `evaluation/benchmarks/<name>/run.sh` | Per-benchmark entry point (sources `run_lib.sh`) |
| `evaluation/benchmarks/<name>/setup.sh` | Idempotent fetch + install |
| `evaluation/benchmarks/<name>/execute.sh` | Raw benchmark script (run by `run_lib.sh` via `incr.sh`) |
| `evaluation/scripts/run_parallel.sh` | Optional heuristic parallel runner (`--only` per benchmark) |
| `evaluation/scripts/verify_outputs.sh` | Diff `*.incr.out` vs `*.incr-observe.out` |
| `evaluation/scripts/restore_benchmark_scripts.sh` | Restore scripts left instrumented by interrupted runs |
| `evaluation/run_results/<size>/` | Timing CSVs and cache sizes written by `run_all.sh` |
| `evaluation/analysis/compare_default_observe.py` | Generate plots; `--skip-dpt`, `--results-dir` |
