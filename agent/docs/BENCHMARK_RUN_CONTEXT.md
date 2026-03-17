# Benchmark Run Context & Best Practices

This document summarizes lessons learned from running the evaluation benchmark suite and provides detailed instructions for reliable, correct benchmark execution in new environments.

---

## Executive Summary

- **Always run `install.sh`** for bio, dpt, file-mod before benchmarking—missing deps cause silent failures and wrong (short) timings.
- **Validate outputs** after runs—empty or truncated outputs indicate failed pipelines.
- **Use polling, not long timeouts** when running benchmarks in background—check every 60–120s.
- **Default mode** (try+strace) gets cache hits within a benchmark run; **observe mode** may not on some machines, making observe slower for dpt.
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

- `run.sh` uses `sudo` for `clean.sh`. Ensure sudo access.
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

## 3. Running Benchmarks

### 3.1 Full Suite

```bash
cd incr

# Both modes (default then observe)
bash evaluation/benchmarks/run.sh

# Single mode
INCR_OBSERVE=0 bash evaluation/benchmarks/run.sh   # default only
INCR_OBSERVE=1 bash evaluation/benchmarks/run.sh # observe only
```

### 3.2 Single Benchmark

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

### 3.3 Background Runs with Polling

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

## 4. Output Validation

### 4.1 Check for Empty Outputs

Many benchmarks write to `outputs/`. Empty files indicate pipeline failure:

```bash
# dpt: db.incr.txt should have lines (e.g. "g: A13 c: 0.30...")
wc -l evaluation/benchmarks/dpt/outputs/db.incr.txt
# Expect: >0 lines

# file-mod: outputs should have .wav or .tar files
ls evaluation/benchmarks/file-mod/outputs/
```

### 4.2 Check stderr for Failures

```bash
# Look for ENOENT, ModuleNotFoundError, "command not found"
tail -50 evaluation/benchmarks/dpt/outputs/dpt_1.sh.incr.err
```

Common failure patterns:

- `ffmpeg: ENOENT` → install ffmpeg
- `samtools: command not found` → run bio/install.sh
- `ModuleNotFoundError: No module named 'torchvision'` → `pip install torchvision`
- `mogrify: command not found` → `apt install imagemagick`

### 4.3 Compare Default vs Observe Outputs

For correctness, compare key output files:

```bash
diff <(head -20 benchmarks/dpt/outputs/db.incr.txt) /path/to/reference.txt
```

---

## 5. Benchmark-Specific Notes

### 5.1 bio

- **Deps**: samtools, minimap2, gnuplot (via install.sh)
- **Verify**: `which samtools`
- **Typical speedup**: observe ~2x faster (e.g. 166s → 88s)

### 5.2 dpt

- **Deps**: torch, torchvision, segment-anything, tensorflow, opencv, ImageMagick
- **Script fix**: dpt_5c, dpt_5d, dpt_5e use `python3 scripts/plot_1.py` (not `python plot_1.py`)
- **Output**: `outputs/db.incr.txt` should have lines like `g: A13 c: 0.30...`
- **Cache**: default gets cache hits for dpt_3a, dpt_3b, dpt_5a–e (same pipeline as dpt_1, dpt_2, dpt_4). Observe may not get hits on some machines.
- **Typical**: default ~591s (with cache), observe ~979s (no cache) on same machine

### 5.3 file-mod

- **Deps**: ffmpeg (via install.sh)
- **Excluded** from run.sh (no min_inputs). Run manually with `--small`.
- **Verify**: `which ffmpeg`
- **Typical speedup**: observe ~2.5x (e.g. 50s → 20s)

### 5.4 nginx-analysis, beginner, covid, etc.

- Use standard tools (grep, awk, sort). No install.sh.
- Usually similar or slightly faster with observe.

---

## 6. Modes: Default vs Observe

| Mode | INCR_OBSERVE | Tracing | When faster |
|------|--------------|---------|-------------|
| default | 0 | try + strace (sandbox) | dpt (cache hits), some read-heavy |
| observe | 1 | observe (ptrace, no sandbox) | bio, file-mod, nlp-ngrams (write-heavy) |

**Observe** runs commands directly (no overlayfs). **Default** uses try overlayfs + strace. Cache keys are the same; cache validity can differ because observe may trace more paths (e.g. /tmp) that change between runs.

---

## 7. Results & Plots

```bash
cd incr/evaluation/analysis
python3 compare_default_observe.py --output-dir ../run_results/plots
```

Outputs: `run_results/plots/default_vs_observe.pdf`, `.png`

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Benchmark finishes in seconds | Missing Python deps (libbash, libdash, shasta) | `pip install libbash libdash shasta` |
| file-mod ~12s total | ffmpeg not installed | `apt install ffmpeg` or run file-mod/install.sh |
| bio fails immediately | samtools not installed | `bash benchmarks/bio/install.sh` |
| dpt db.incr.txt empty | torchvision or segment_anything missing | `pip install torchvision segment-anything` |
| dpt plot_3.py: No such file | Wrong path in script | Use `python3 scripts/plot_3.py` |
| observe much slower than default (dpt) | Observe not getting cache hits | Expected on some machines; default uses sandbox |
| Command timeout / hang | Long-running benchmark | Use background + polling, not single long timeout |

---

## 9. Quick Setup for New Machine

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

# 5. Verify tools
which ffmpeg samtools mogrify
python3 -c "import torchvision, segment_anything; print('OK')"

# 6. Run (use background + polling for long benchmarks)
bash evaluation/benchmarks/run.sh
```

---

## 10. Parallel Runner & Monitoring

### 10.1 run_parallel.sh

Run all benchmarks in parallel (each runs default then observe in its own process):

```bash
cd incr
bash evaluation/scripts/run_parallel.sh              # all benchmarks including dpt
bash evaluation/scripts/run_parallel.sh --skip-dpt   # skip dpt (longest, ~10+ min)
```

Results: `evaluation/run_results_parallel/default/`, `evaluation/run_results_parallel/observe/`. Committed alongside `run_results/`.

### 10.2 monitor_benchmarks.sh

Poll status while parallel run is in progress:

```bash
bash evaluation/scripts/monitor_benchmarks.sh           # one-shot status
bash evaluation/scripts/monitor_benchmarks.sh --loop   # refresh every 60s
```

### 10.3 Plotting (with or without dpt)

```bash
cd evaluation/analysis
python3 compare_default_observe.py --skip-dpt --output-dir ../run_results_parallel/plots
```

- `--skip-dpt`: exclude dpt from plot/summary
- `--results-dir`: optional; auto-detects `run_results_parallel` if present

---

## 11. Output Verification

### 11.1 verify_outputs.sh

Verify that default and observe produce identical outputs (validates speedups):

```bash
cd incr
bash evaluation/scripts/verify_outputs.sh --min      # faster, uses --min for benchmarks
bash evaluation/scripts/verify_outputs.sh            # uses --small
bash evaluation/scripts/verify_outputs.sh --no-cleanup  # keep artifacts for inspection
```

- Uses `timeout` (180s per benchmark) if available to avoid hangs
- Compares all output files except `timing.csv` and `*.err`
- Cleans up on exit: restores benchmark scripts (via `restore_benchmark_scripts.sh`), removes `verify_outputs/`, benchmark cache/outputs, `/tmp` artifacts

---

## 12. Observe-Mode Optimization

**OBSERVE_READ_EXCLUDED_PATHS** (in `incr/src/config.rs`): filters `/tmp`, `/dev`, `/proc`, `/sys` from observe-mode read dependencies at parse time. Observe runs without sandbox and traces more paths; these cause cache invalidation. Filtering improves cache hits for observe (e.g. nlp-ngrams, bio).

---

## 13. Artifact Cleanup

Manual cleanup after runs:

```bash
cd incr/evaluation

# Benchmark caches and outputs
for b in beginner bio covid dpt nginx-analysis nlp-uppercase nlp-ngrams poet spell unixfun weather word-freq; do
  sudo rm -rf benchmarks/$b/cache benchmarks/$b/outputs
done

# Parallel run artifacts
rm -rf parallel_logs run_results_parallel verify_outputs

# /tmp artifacts
rm -rf /tmp/sort* /tmp/tmp* /tmp/cache* /tmp/incr_bench* /tmp/dpt*.log
```

---

## 14. Files Reference

| Path | Purpose |
|------|---------|
| `evaluation/benchmarks/run.sh` | Main runner; skips image-annotation, file-mod |
| `evaluation/scripts/run_parallel.sh` | Parallel runner; `--skip-dpt` to skip dpt |
| `evaluation/scripts/monitor_benchmarks.sh` | Poll parallel run status; `--loop` for refresh |
| `evaluation/scripts/verify_outputs.sh` | Verify default vs observe output correctness |
| `evaluation/scripts/restore_benchmark_scripts.sh` | Restore benchmark scripts if left in incr mode; removes `incr_script_*` files |
| `evaluation/benchmarks/<name>/execute.sh` | Per-benchmark runner |
| `evaluation/benchmarks/<name>/install.sh` | Dependency installer |
| `evaluation/run_results/default/`, `observe/` | timing CSV (sequential run) |
| `evaluation/run_results_parallel/` | timing CSV (parallel run) |
| `evaluation/analysis/compare_default_observe.py` | Generate plots; `--skip-dpt`, `--results-dir` |
