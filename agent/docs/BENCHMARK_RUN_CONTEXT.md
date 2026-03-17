# Benchmark Run Context & Best Practices

This document summarizes lessons learned from running the evaluation benchmark suite and provides detailed instructions for reliable, correct benchmark execution in new environments.

---

## Executive Summary

- **Use `run_parallel.sh`** as the primary way to run benchmarks. Results go to `run_results_parallel/`.
- **Default baseline**: `run_results_parallel/default/` contains timing CSVs. Use these as the reference for correctness.
- **Always run `restore_benchmark_scripts.sh`** before benchmarking—incr overwrites scripts in place; interrupted runs can leave scripts empty (e.g. word-freq wf.sh).
- **Always run `install.sh`** for bio, dpt, file-mod before benchmarking—missing deps cause silent failures and wrong (short) timings.
- **Validate outputs** after runs—empty or truncated outputs indicate failed pipelines. Compare timings to baseline; suspiciously short times (e.g. word-freq <1s) indicate failure.
- **Excluded benchmarks**: image-annotation (OpenAI key), file-mod (no min_inputs—use --small).

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

- `run.sh` and `run_parallel.sh` use `sudo` for `clean.sh`. Ensure sudo access.
- mergerfs (for try overlayfs) when using default mode: `sudo apt install mergerfs`

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

### 3.1 Recommended: Parallel Runner (Primary)

**This is the recommended way to run benchmarks.** Results are written to `run_results_parallel/`.

```bash
cd incr

# Restore any broken scripts first (incr overwrites in place; interrupted runs can leave scripts empty)
bash evaluation/scripts/restore_benchmark_scripts.sh

# Run all benchmarks (default + observe for each)
bash evaluation/scripts/run_parallel.sh              # all benchmarks including dpt
bash evaluation/scripts/run_parallel.sh --skip-dpt  # skip dpt (longest, ~10+ min)
```

**Results:**
- `evaluation/run_results_parallel/default/<bench>-time.csv` — default mode timings
- `evaluation/run_results_parallel/observe/<bench>-time.csv` — observe mode timings
- `evaluation/parallel_logs/<bench>_default.log`, `<bench>_observe.log` — run logs

**Parallel runner behavior:**
- Runs benchmarks in batches of 3 to avoid resource contention
- **word-freq runs first** (it fails when run alongside many others)
- Cleans caches between batches to free disk space
- Cleans up on exit: restores scripts, removes cache/outputs

### 3.2 Sequential Runner (Optional)

For single-benchmark debugging or when parallel is not desired:

```bash
cd incr
bash evaluation/benchmarks/run.sh
```

Results go to `evaluation/run_results/default/` and `observe/` (created by run.sh).

### 3.3 Single Benchmark

```bash
cd incr/evaluation

# Clean first
sudo bash benchmarks/<name>/clean.sh
rm -rf benchmarks/<name>/cache benchmarks/<name>/outputs
mkdir -p benchmarks/<name>/outputs

# Run
export INCR_OBSERVE=0  # or 1 for observe
bash benchmarks/<name>/execute.sh --small --incr-only
```

### 3.4 Background Runs with Polling

**Do not** use long blocking timeouts. Use background + periodic checks:

```bash
# Start
nohup bash -c 'export INCR_OBSERVE=0; bash benchmarks/dpt/execute.sh --small --incr-only' > /tmp/dpt.log 2>&1 &
PID=$!
echo "Started PID: $PID"

# Poll every 60–120s
sleep 120
tail -20 /tmp/dpt.log
wc -l benchmarks/dpt/outputs/timing.csv
ps -p $PID -o pid,etime || echo "Process ended"
```

---

## 4. Default Baseline & Error Checking

### 4.1 Default Baseline

The **default baseline** is `run_results_parallel/default/`. Each file `<bench>-time.csv` contains per-script timings:

```csv
mode,script,time_sec
incr,wf.sh,5.506
incr,top-n.sh,0.202
```

Use these as the reference for correctness. After a new run, compare your timings to the baseline.

### 4.2 Detecting Wrong Results

**Suspiciously short times indicate failure.** Examples:

| Benchmark | Script | Baseline (approx) | Suspicious (wrong) |
|-----------|--------|-------------------|---------------------|
| word-freq | wf.sh | ~5.5s | <1s (empty output) |
| word-freq | top-n.sh | ~0.2s | ~0.1s (if wf.sh failed) |
| bio | bio-1.sh | ~7–50s | <1s |
| dpt | dpt_1.sh | ~194s | <5s |

If a script's time is **much shorter** than the baseline (e.g. 10x+), the run likely failed.

### 4.3 How to Check for Errors

1. **Compare timings** to `run_results_parallel/default/`:
   ```bash
   # After running, compare a benchmark
   diff run_results_parallel/default/word-freq-time.csv /path/to/your/word-freq-time.csv
   # Or manually: if wf.sh shows 0.08s instead of ~5.5s, something is wrong
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

Results live in `run_results_parallel/`:

```bash
cd incr/evaluation/analysis
python3 compare_default_observe.py --skip-dpt --output-dir ../run_results_parallel/plots
```

Outputs: `run_results_parallel/plots/default_vs_observe.pdf`, `.png`

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
cd evaluation/analysis
python3 compare_default_observe.py --skip-dpt --output-dir ../run_results_parallel/plots
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

# 2. Python deps
pip install --user libbash libdash shasta

# 3. Fetch inputs
cd incr
for b in evaluation/benchmarks/*/; do
  [ -f "${b}fetch.sh" ] && bash "${b}fetch.sh" --small
done

# 4. Install benchmark deps
bash evaluation/benchmarks/bio/install.sh
bash evaluation/benchmarks/dpt/install.sh
bash evaluation/benchmarks/file-mod/install.sh

# 5. Restore scripts (in case of prior interrupted runs)
bash evaluation/scripts/restore_benchmark_scripts.sh

# 6. Verify tools
which ffmpeg samtools mogrify
python3 -c "import torchvision, segment_anything; print('OK')"

# 7. Run benchmarks (recommended: parallel)
bash evaluation/scripts/run_parallel.sh --skip-dpt

# 8. Verify outputs
bash evaluation/scripts/verify_outputs.sh

# 9. Check baseline: compare run_results_parallel/default/*.csv to expected timings
```

---

## 14. Artifact Cleanup

Manual cleanup (run_results_parallel is kept; clean caches and logs if needed):

```bash
cd incr/evaluation

# Benchmark caches and outputs (keeps run_results_parallel)
for b in beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq; do
  sudo rm -rf benchmarks/$b/cache benchmarks/$b/outputs
done

# Logs (optional)
rm -rf parallel_logs verify_outputs

# /tmp artifacts
rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* /tmp/dpt*.log
```

---

## 15. Files Reference

| Path | Purpose |
|------|---------|
| `evaluation/scripts/run_parallel.sh` | **Primary** parallel runner; `--skip-dpt` to skip dpt |
| `evaluation/benchmarks/run.sh` | Sequential runner; skips image-annotation, file-mod |
| `evaluation/scripts/monitor_benchmarks.sh` | Poll parallel run status; `--loop` for refresh |
| `evaluation/scripts/verify_outputs.sh` | Verify default vs observe output correctness |
| `evaluation/scripts/restore_benchmark_scripts.sh` | Restore scripts (incr + empty); run before benchmarking |
| `evaluation/benchmarks/<name>/execute.sh` | Per-benchmark runner |
| `evaluation/benchmarks/<name>/install.sh` | Dependency installer |
| `evaluation/run_results_parallel/default/`, `observe/` | **Default baseline** timing CSVs (parallel run) |
| `evaluation/analysis/compare_default_observe.py` | Generate plots; `--skip-dpt`, `--results-dir` |
