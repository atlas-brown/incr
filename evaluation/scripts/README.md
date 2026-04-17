# Evaluation Scripts

Helper scripts for running and verifying benchmarks. Run from `incr/` root.

Scripts that drive benchmarks **clean up on exit** (including Ctrl+C): they call `restore_benchmark_scripts.sh` and remove caches/temp files where noted.

## Primary workflow

| Command | Purpose |
|---------|---------|
| `bash evaluation/benchmarks/run_all.sh ...` | **Canonical** full orchestrator (setup, per-benchmark `run.sh`, results under `run_results/`) |
| `bash evaluation/run.sh ...` | Thin wrapper; forwards all args to `run_all.sh` |

## Helper scripts

| Script | Purpose |
|--------|---------|
| `run_smoke_min.sh` | Runs `run_all.sh --mode easy --size min --run-mode all` (optional extra args) |
| `verify_outputs.sh` | Diff `*.incr.out` vs `*.incr-observe.out` under `benchmarks/*/outputs/<size>/`. Use `--run` to invoke `run_all` first |
| `run_parallel.sh` | Runs one `run_all.sh --only <bench>` per benchmark in parallel batches (heuristic; not the default) |
| `run_bench_background.sh` | `nohup run_all.sh` with log under `evaluation/bench_run.log` |
| `restore_benchmark_scripts.sh` | Restore instrumented scripts via git + remove `incr_script_*` / sentinels |
| `monitor_benchmarks.sh` | Poll parallel logs (adjust paths if you change `run_parallel.sh`) |
| `check_bench_progress.sh` | Progress helper for background runs |

## Quick start

```bash
cd incr
bash evaluation/benchmarks/run_all.sh --mode easy --size min --run-mode all
```

```bash
# Optional: parallel (after inputs are built)
bash evaluation/scripts/run_parallel.sh --min --run-mode both --skip-dpt
```
