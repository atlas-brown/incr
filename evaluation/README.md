# incr Evaluation Suite

End-to-end shell benchmarks aligned with `incr/main/benchmarks/` for mergeability. The **canonical entry point** is `evaluation/benchmarks/run_all.sh`.

## Run modes (`--run-mode`)

| Mode | Meaning |
|------|--------|
| `bash` | Baseline: plain `bash script.sh` |
| `incr` | `INCR_OBSERVE=0` — try + strace (no observe) |
| `incr-observe` | `INCR_OBSERVE=1` — observe when `../observe/target/release/observe` exists |
| `both` | `bash` then `incr` per script |
| `all` | `bash`, then `incr`, then `incr-observe` per script (full comparison) |

## Structure

```
evaluation/
├── run.sh                      # Thin wrapper → benchmarks/run_all.sh
├── benchmarks/
│   ├── run_all.sh              # Orchestrator (setup + per-benchmark run.sh)
│   ├── run_lib.sh              # Shared helpers (timing, restore, cleanup)
│   ├── <benchmark>/run.sh      # Per-benchmark runner
│   ├── <benchmark>/setup.sh    # install + fetch inputs
│   ├── <benchmark>/execute.sh  # Legacy manual runner (optional)
│   └── <benchmark>/scripts/    # Benchmark scripts
├── run_results/<size>/         # Copied timing CSVs + cache sizes
├── scripts/                    # verify_outputs, run_parallel, smoke, etc.
└── analysis/                   # Plotting helpers
```

## Running (from `incr/`)

```bash
# EASY suite (12 benchmarks), min inputs, bash + incr + incr-observe
bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all

# Same via wrapper
bash evaluation/run.sh --mode easy --size min --run-mode all

# Subset
bash evaluation/benchmarks/run_all.sh --only covid,bio --size min --run-mode both --skip-setup

# Full suite (+ dpt, image-annotation)
bash evaluation/benchmarks/run_all.sh --mode full --size small --run-mode both
```

**Results:** `evaluation/run_results/min/` (or `small/`) — `*-time.csv`, `*-size.txt`.

**War-and-peace** (standalone):

```bash
bash evaluation/war-and-peace/with_cache.sh
bash evaluation/war-and-peace/with_cache_observe.sh
bash evaluation/war-and-peace/without_cache.sh
```

## Documentation

See `agents/docs/BENCHMARK_RUN_CONTEXT.md` and `agents/docs/EVALUATION_BENCHMARK_SUITE.md`.
