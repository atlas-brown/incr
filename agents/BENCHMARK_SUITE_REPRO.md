# Full benchmark suite reproduction (draft for INSTRUCTIONS.md)

This document is a **working draft** for updating the **Results reproducible** / benchmark sections in root [`INSTRUCTIONS.md`](../INSTRUCTIONS.md). It reflects the current harness under [`evaluation/benchmarks/`](../evaluation/benchmarks/) (`run_all.sh`, per-benchmark `setup.sh` / `run.sh`, `verify_outputs.sh`, `show_results.py`).

**Note:** The older one-line entry in `INSTRUCTIONS.md` that points to `bash ./run.sh` inside `evaluation/benchmarks` is **obsolete**. The supported driver is **`run_all.sh`** (or each benchmark’s own `run.sh`).

---

## What the suite measures

The suite runs real shell pipelines under **plain `bash`** and under **`incr`** (via [`incr.sh`](../incr.sh)), times each script, and optionally verifies that **stdout matches** between the two modes. Timing CSVs are aggregated under **`evaluation/run_results/<size>/`**.

**Paper ↔ repository names** (keep in any user-facing doc):

| Paper (informal) | Benchmark directory |
|------------------|----------------------|
| dict | `word-freq` |
| ngram | `nlp-ngrams` |
| uppercase | `nlp-uppercase` |
| unixgame | `unixfun` |
| nginx | `nginx-analysis` |
| image | `image-annotation` |

---

## Prerequisites

1. **OS:** Linux (tested on Ubuntu 20.04+; Ubuntu 22.04 matches much of the paper setup).
2. **Tools:** `bash`, `git`, `python3`, `pip3`, `cargo` (Rust), `sudo` (for apt in `setup.sh`, overlay cleanup, `ptrace`).
3. **System packages** (see also root [`README.md`](../README.md)):

   ```sh
   sudo apt update
   sudo apt install mergerfs strace python3-pip
   ```

4. **Rust build** from repository root:

   ```sh
   cargo build --release
   ```

   [`incr.sh`](../incr.sh) invokes `target/release/incr`.

5. **Python dependencies** for [`src/scripts/insert.py`](../src/scripts/insert.py):

   ```sh
   pip3 install --no-cache-dir -r requirements.txt
   ```

6. **`strace` / ptrace:** Incr uses `strace`; Yama must allow ptracing:

   ```sh
   echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
   ```

7. **Spell benchmark:** `setup.sh` installs `wamerican` if `/usr/share/dict/words` is missing (needed for `comm` in some scripts).

---

## One-command drivers

All commands below assume:

```sh
cd evaluation/benchmarks
```

### Easy mode (12 benchmarks — no GPU, no API keys)

**Default** is `--mode easy --size min` (tiny inputs, fastest sanity check):

```sh
bash run_all.sh
# equivalent:
bash run_all.sh --mode easy --size min --run-mode both
```

**Evaluation-sized inputs** (`small`):

```sh
bash run_all.sh --mode easy --size small --run-mode both
```

**Wall time (observed ballpark):** `min` often **~5–20+ minutes** (network for first-time downloads). `small` often **~1–2 hours** on a strong machine; allow **several hours** on slower disks or under load. Per-benchmark wall limit defaults to **14400 s** (4 hours): `--timeout=SECS` to override.

### Full mode (14 benchmarks)

Adds **`dpt`** (PyTorch + Segment Anything + large model) and **`image-annotation`** (API key + `llm` CLI). Example:

```sh
# Example only — install deps per each benchmark’s README/setup first
bash run_all.sh --mode full --size small --run-mode both
```

---

## Output verification (bash vs incr)

To **diff stdout** between bash and incr, you need paired **`*.bash.out`** and **`*.incr.out`** under `evaluation/benchmarks/<name>/outputs/<size>/`.

- For **`--size min`**, `run_all.sh` **keeps** `outputs/` by default — you can run verification immediately after `run_all`.
- For **`--size small`**, the default is to **delete** `outputs/` after each benchmark to save disk. For verification, run:

```sh
bash run_all.sh --mode easy --size small --run-mode both --no-clear-outputs
```

Reserve **tens of GB** free if you retain all small outputs (inputs + stdout can be large; see [`agents/EVALUATION.md`](EVALUATION.md) disk table).

Then:

```sh
bash verify_outputs.sh --mode easy --size min
bash verify_outputs.sh --mode easy --size small
```

Exit code **0** means paired outputs match and stderr sanity checks pass (with **`file-mod`** excluded from ffmpeg-banner false positives). Exit **non-zero** means mismatches, missing pairs, or suspicious htslib/samtools error lines in `*.err`.

---

## Printing timing tables

From `evaluation/benchmarks/`:

```sh
python3 show_results.py --size min
python3 show_results.py --size small
python3 show_results.py --size small --detail
```

Reads copied CSVs from **`evaluation/run_results/<size>/*-time.csv`** (written by `run_all.sh`).

Optional comparison to checked-in baselines (if present):

```sh
python3 compare_to_baseline.py
```

---

## `run_all.sh` options (reference)

| Option | Meaning |
|--------|---------|
| `--mode easy\|full` | `easy`: 12 benchmarks. `full`: + `dpt`, `image-annotation`. |
| `--size min\|small` | Input scale; `min` is for quick validation. |
| `--run-mode bash\|incr\|both` | What to time (default `both`). |
| `--only=a,b,c` | Subset of benchmark directory names. |
| `--skip-setup` | Skip `setup.sh` (data must already exist). |
| `--clear-cache` / `--no-clear-cache` | Clear each benchmark’s `cache/` after run (default: clear). |
| `--clear-outputs` / `--no-clear-outputs` | Clear `outputs/` after each benchmark. For `small`, default is **clear** unless you pass `--no-clear-outputs`. |
| `--timeout=SECS` | Per-benchmark timeout (default 14400). |
| `--results-dir=DIR` | Override aggregated results root (default `evaluation/run_results`). |

**Harness behavior (stability):** `run_lib.sh` redirects **stdin from `/dev/null`** for both bash and incr (avoids hangs when stdin is a non-closing pipe). With `--run-mode both`, bash and incr run **interleaved per script** to avoid filling disk with huge bash-only stdout before incr runs. `TMPDIR=/tmp` during timed scripts; best-effort `/tmp` cleanup after each script.

---

## Cleaning a full re-run from scratch

To remove cached runs, outputs, and downloaded inputs for a **cold** reproduction:

1. For each benchmark (or only those you care about), remove **`cache/`**, **`outputs/`**, **`inputs/`** (or run each benchmark’s **`clean.sh`** where present, then remove `inputs/` if you need a full re-fetch).
2. Remove **`evaluation/run_results/`** (generated; often gitignored).
3. Remove stray **`scripts/*.incr_orig`** and **`incr_script_*.sh`** under benchmark `scripts/` if interrupted runs left them.
4. Unmount stale overlay mounts under `/tmp` if needed (`run_all.sh` pre-run cleanup attempts this).

**Beginner `small`:** input preparation checks for **~32 GiB** free before large log download/merge; a partial `inputs/nginx-logs_small` after a failed run should be removed before retry.

---

## Related harnesses (not the 14-scenario driver)

- **Bash test suite equivalence:** [`evaluation/bash-ts/run.sh`](../evaluation/bash-ts/run.sh) — see `INSTRUCTIONS.md` behavioral equivalence section.
- **Single demo pipeline:** [`evaluation/war-and-peace/`](../evaluation/war-and-peace/) — `without_incr.sh` vs `with_incr.sh`.
- **Legacy / paper scripts:** Cold-start and optimization plots may reference `evaluation/analysis/` or external `incr-paper` data; wire those explicitly when documenting paper figures.

---

## Validation log (automated run, for maintainers)

The following end-to-end check was run successfully on this repository:

1. Cleared easy-benchmark **`cache/`**, **`outputs/`**, **`inputs/`**, **`evaluation/run_results/`**, sentinels, and best-effort overlay/`/tmp` cleanup.
2. `cargo build --release`, `pip3 install -r requirements.txt`, `ptrace_scope=0`.
3. **`bash run_all.sh --mode easy --size min --run-mode both`** → 12 passed; **`verify_outputs.sh --mode easy --size min`** → OK (82 script pairs).
4. **`bash run_all.sh --mode easy --size small --run-mode both --no-clear-outputs`** → 12 passed; **`verify_outputs.sh --mode easy --size small`** → OK (82 script pairs).

Use this section as a template for future “artifact smoke test” notes when updating `INSTRUCTIONS.md`.
