# Pending Benchmark Run Steps

This document captures the remaining steps from the full benchmark run plan, to be resumed after investigating dpt performance (see note at bottom).

---

## Prerequisites (already done)

- `restore_benchmark_scripts.sh` retired; replaced by `restore_sentinels.sh`
- dpt deps installed: `torch`, `torchvision`, `segment-anything`, `tensorflow`, `opencv-python`
- image-annotation deps installed: `llm`, `llm-interpolate`, `llm-clap`, `llm-ollama`
- Scripts compared against `main/`: only known diff is `python3 scripts/plot_*.py` vs `python plot_*.py` in eval (eval is correct)
- All benchmark artifacts cleaned; 39G free on disk

---

## Step A — Test dpt in min mode

```bash
cd incr
bash evaluation/benchmarks/run_all.sh --only dpt --mode full --size min --run-mode all
```

`setup.sh` downloads `models.zip` (~2 GB, one-time) from `atlas.cs.brown.edu` → `inputs/models/`;
copies `min_inputs/dpt.min` → `inputs/dpt.min`.

Runs 10 scripts × 3 modes (`bash`, `incr`, `incr-observe`). dpt is slow (~5 min/script in bash).

**Verification**: check non-empty outputs (ML outputs are non-deterministic; do not exact-diff):

```bash
wc -l evaluation/benchmarks/dpt/outputs/min/dpt_*.bash.out
wc -l evaluation/benchmarks/dpt/outputs/min/dpt_*.incr.out
wc -l evaluation/benchmarks/dpt/outputs/min/dpt_*.incr-observe.out
```

---

## Step B — Test image-annotation in min mode

```bash
bash evaluation/benchmarks/run_all.sh --only image-annotation --mode full --size min --run-mode all
```

`setup.sh` copies 5 bundled JPEGs from `min_inputs/` → `inputs/jpg.min/jpg`.
Runs 7 scripts × 3 modes. Each script calls `llm -m gpt-4o-mini` (OPENAI_API_KEY must be set).

**Verification**: scripts should exit cleanly (exit code 0) and produce non-empty output.
LLM output is non-deterministic — do not diff `incr.out` vs `incr-observe.out`.

---

## Step C — Full suite, small inputs

```bash
bash evaluation/benchmarks/run_all.sh --mode full --size small --run-mode all
```

Key behavior for `--size small`:
- `CLEAR_OUTPUTS=1` by default — outputs removed after each benchmark (prevents disk filling)
- `CLEAR_CACHE=1` by default — cache cleared after each benchmark
- Timing CSVs copied to `evaluation/run_results/small/<benchmark>-time.csv` before clearing

For `dpt --small`: `fetch.sh` downloads `pl-06-P_F-A_N-20250401T083751Z-001.zip` from `atlas.cs.brown.edu`.
For `image-annotation --small`: downloads `jpg.zip` (10 images) from `atlas-group.cs.brown.edu`.

No output verification for this run (outputs auto-deleted + LLM non-determinism).

---

## Step D — Commit and push

```bash
cd incr
git add evaluation/run_results/ evaluation/scripts/ agents/
git commit -m "Add full benchmark suite results (min + small, all 14 benchmarks)"
git push origin observe
```

Includes:
- `evaluation/run_results/min/` — 12 EASY benchmark CSVs (already run)
- `evaluation/run_results/small/` — all 14 benchmark CSVs (from Step C)
- `evaluation/scripts/restore_sentinels.sh` — new script (replaces deleted `restore_benchmark_scripts.sh`)
- `agents/` updates (docs, test fixes from this session)

---

## Step E — Generate visualizations

```bash
cd incr/evaluation/analysis

# Small inputs (primary results)
python3 compare_default_observe.py --results-dir ../run_results/small

# Min inputs (for reference)
python3 compare_default_observe.py --results-dir ../run_results/min --output-dir plots_min
```

Outputs `plots/default_vs_observe.png` and `.pdf` comparing `incr` (try+strace) vs `incr-observe`
totals per benchmark. Use `--skip-dpt` if dpt timings are outliers that compress the chart scale.

---

## Note: dpt incr-observe performance investigation

During the aborted min run, `incr-observe` on `dpt_3a.sh` was observed to be much slower
than `incr` (try+strace). This warrants investigation before committing the full small run results.

`dpt_3a.sh` is `scripts/dpt_3a.sh` in `evaluation/benchmarks/dpt/scripts/`.

Possible causes:
- Observe may not be getting cache hits due to `/tmp`-path or other excluded-path reads changing
  between the incr run and the incr-observe run
- `dpt_3a.sh` may involve large file writes/reads that observe traces differently
- `OBSERVE_READ_EXCLUDED_PATHS` filtering may cause different cache key computation

Investigate with: compare `outputs/min/dpt_3a.sh.incr.out` vs `dpt_3a.sh.incr-observe.out` and
examine stderr for cache miss/hit indicators.
