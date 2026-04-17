# Evaluation Suite – Push Summary

## Changes in This Push

### 1. Observe-mode optimization
- **OBSERVE_READ_EXCLUDED_PATHS** in `incr/src/config.rs`: filters `/tmp`, `/dev`, `/proc`, `/sys` from observe-mode read dependencies at parse time
- Improves cache hits for observe (e.g. nlp-ngrams ~4x, bio ~3x faster)

### 2. File structure cleanup
- **scripts/** – helper scripts moved here:
  - `run_parallel.sh` – parallel benchmark run, `--skip-dpt` to skip longest
  - `monitor_benchmarks.sh` – poll status, `--loop` for refresh
  - `verify_outputs.sh` – verify default vs observe outputs match
  - `run_smoke_min.sh`, `run_bench_background.sh`, `check_bench_progress.sh`
- **Removed**: `verify_bio_ngrams.sh`, `verify_speedup.sh` (superseded by `verify_outputs.sh`)
- **Added**: `evaluation/.gitignore` for artifact dirs

### 3. Plotting
- `compare_default_observe.py`: `--skip-dpt`, `--results-dir`; auto-detects `run_results_parallel`

### 4. Documentation
- **BENCHMARK_RUN_CONTEXT.md** – parallel runner, verification, cleanup, artifact paths
- **README.md** – structure overview, updated run commands
- **scripts/README.md** – script reference

## Verification

All 11 benchmarks (beginner, bio, covid, nginx-analysis, nlp-uppercase, nlp-ngrams, poet, spell, unixfun, weather, word-freq) verified: **default and observe produce identical outputs**.

## Quick Start

```bash
cd incr
bash evaluation/scripts/run_parallel.sh --skip-dpt
bash evaluation/scripts/monitor_benchmarks.sh --loop
```

## Files to Commit

```
incr/src/config.rs                         # OBSERVE_READ_EXCLUDED_PATHS
incr/src/scripts/parse_observe.rs         # observe path filtering
incr/evaluation/scripts/                   # run_parallel, monitor, verify_outputs, etc.
incr/evaluation/scripts/README.md
incr/evaluation/.gitignore
incr/evaluation/README.md
incr/evaluation/PUSH_SUMMARY.md
incr/agents/docs/BENCHMARK_RUN_CONTEXT.md
incr/evaluation/analysis/compare_default_observe.py
```

Deleted: `incr/evaluation/verify_bio_ngrams.sh`, `incr/evaluation/verify_speedup.sh`
