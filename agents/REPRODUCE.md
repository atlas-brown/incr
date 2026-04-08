# Reproducing the benchmark suite (`REPRODUCE.md`)

Technical reference and **drafting guide** for the **“Results reproducible” → re-execution / benchmark suite** part of root [`INSTRUCTIONS.md`](../INSTRUCTIONS.md).

**You can treat this file as self-contained:** an agent or author who has **only** this document (plus the ability to open paths it names) should be able to write a solid **“Re-execution performance”** subsection and fix the **obsolete benchmark driver** paragraphs in `INSTRUCTIONS.md` without guessing repository history.

---

## For agents drafting `INSTRUCTIONS.md`

### Goal

Produce reviewer-facing steps that reproduce **end-to-end benchmark timing and bash↔incr stdout agreement** using the current harness: [`evaluation/benchmarks/run_all.sh`](../evaluation/benchmarks/run_all.sh), per-benchmark [`setup.sh`](../evaluation/benchmarks/) / [`run.sh`](../evaluation/benchmarks/), [`verify_outputs.sh`](../evaluation/benchmarks/verify_outputs.sh), [`show_results.py`](../evaluation/benchmarks/show_results.py).

### Scope: what this document covers vs what it does not

| Topic | Covered here? | Where it usually lives in `INSTRUCTIONS.md` |
|-------|----------------|---------------------------------------------|
| Running the **14 benchmark directories** under `evaluation/benchmarks/<name>/`, timing bash vs incr, aggregating CSVs, verifying stdout | **Yes** | **Re-execution performance** — replace obsolete “`bash ./run.sh` / `execute.sh`” text using this file. |
| **Cold-start overhead** plots, `incr-paper` CSVs | **No** | Keep existing subsection or point to `evaluation/analysis/` and paper bundle. |
| **Bash test suite** (`evaluation/bash-ts`) | **No** (only a pointer) | **Behavioral equivalence** subsection. |
| **Runtime optimizations** (eager streams, introspection, compaction) | **No** | Separate subsection; may need microbenchmark scripts not described here. |
| **Optional annotations** | **No** | Separate subsection; involves CLI flags and optional corpora. |
| Docker / **war-and-peace** / single-command `incr` demo | **No** | **Artifact functional** / exercisability — already in `INSTRUCTIONS.md`. |

Do **not** merge cold-start or bash-ts instructions into the re-execution section unless the editor explicitly wants one long section; cross-links are clearer.

### Obsolete text in `INSTRUCTIONS.md` to replace

The following (or anything equivalent) is **misleading for reviewers** and should be updated:

- Presenting **only** [`evaluation/benchmarks/run.sh`](../evaluation/benchmarks/run.sh) as *the* benchmark driver. That file **exists** but is **legacy**: it loops benchmarks, calls each **`execute.sh`**, and does **not** integrate the current **`setup.sh` / per-benchmark `run.sh`** flow, **`min`** inputs, **`verify_outputs.sh`**, or the interleaved bash/incr behavior in [`run_lib.sh`](../evaluation/benchmarks/run_lib.sh).

- Claiming the only per-benchmark entrypoint is **`execute.sh`**. The **supported** harness uses each directory’s **`setup.sh`** (fetch/deps) and **`run.sh`** (timed bash vs incr), orchestrated by **`run_all.sh`**.

**What reviewers should run:** `cd evaluation/benchmarks` then **`bash run_all.sh`** (with flags below). Mention the legacy `run.sh` + `execute.sh` path only as deprecated if you document history.

### Glossary (use these terms consistently in `INSTRUCTIONS.md`)

| Term | Meaning |
|------|---------|
| **`run_all.sh`** | Global driver: runs `setup.sh --<size>` for each selected benchmark, then each benchmark’s **`run.sh`** to time scripts. |
| **Per-benchmark `run.sh`** | Lives in `evaluation/benchmarks/<name>/run.sh`; times scripts listed for that scenario. Not the same as `run_all.sh`. |
| **Legacy top-level `evaluation/benchmarks/run.sh`** | Old loop over benchmarks invoking **`execute.sh`**; do not use for artifact instructions unless reproducing an old baseline on purpose. |
| **`execute.sh`** | Legacy per-benchmark runner still present in many directories; superseded for docs by **`setup.sh` + `run.sh`** under **`run_all.sh`**. |
| **`--mode easy`** | Twelve benchmarks with no GPU and no paid API: `beginner`, `bio`, `covid`, `file-mod`, `nginx-analysis`, `nlp-ngrams`, `nlp-uppercase`, `poet`, `spell`, `unixfun`, `weather`, `word-freq`. |
| **`--mode full`** | Same as easy **plus** `dpt` (PyTorch + SAM + model) and `image-annotation` (API key + `llm` CLI). Requires extra setup. |
| **`--size min`** | Tiny / validation inputs; faster; default output retention allows easy verification. |
| **`--size small`** | Larger, paper-style inputs; long wall time; **default clears `outputs/`** after each benchmark unless **`--no-clear-outputs`**. |
| **`--run-mode both`** | Time **bash** and **incr** for each script (default). Needed before `verify_outputs.sh` can compare stdout. |

### Full list of benchmark directory names (14)

Use this exact list when updating the bullet list in `INSTRUCTIONS.md` (same names as directories under `evaluation/benchmarks/`):

`beginner`, `bio`, `covid`, `dpt`, `file-mod`, `image-annotation`, `nginx-analysis`, `nlp-uppercase`, `nlp-ngrams`, `poet`, `spell`, `unixfun`, `weather`, `word-freq`

**Paper ↔ repository** (for the terminology paragraph):

| Paper (informal) | Directory |
|------------------|-----------|
| dict | `word-freq` |
| ngram | `nlp-ngrams` |
| uppercase | `nlp-uppercase` |
| unixgame | `unixfun` |
| nginx | `nginx-analysis` |
| image | `image-annotation` |

Note: **“music”** (if mentioned in the paper) is not wired to the current `run_all.sh` driver; say so or omit until wired.

### What “success” looks like (for prose in `INSTRUCTIONS.md`)

After a successful **`run_all.sh`**:

- **`evaluation/run_results/<size>/`** contains per-benchmark **`*-time.csv`** (and optionally **`*-size.txt`** cache size lines).
- After **`verify_outputs.sh`**: exit code **0**, message like **`OK: all outputs match`**, and a count of checked script pairs (easy mode typically **82** pairs across 12 benchmarks when all scripts run).

Failure modes to mention briefly: setup skipped benchmarks (`FAILED_SETUP`), disk full in `*.err`, `ptrace` denied until `ptrace_scope` is set.

### Paste-ready draft: “Re-execution performance” body

Use as a starting point; replace `XXX` with paper-specific numbers and figure references when known.

```markdown
## Re-execution performance

**Goal:** Measure end-to-end runtimes under plain Bash and under Incr for the benchmark scenarios, and check that Incr reproduces Bash stdout on those workloads.

**Prerequisites:** From the repository root, install dependencies, build Incr, enable ptrace for `strace`, and install Python packages for script rewriting:

```sh
sudo apt update && sudo apt install mergerfs strace python3-pip
pip3 install --no-cache-dir -r requirements.txt
cargo build --release
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

**Driver:** Use **`evaluation/benchmarks/run_all.sh`**. A legacy **`evaluation/benchmarks/run.sh`** still exists and calls each benchmark’s **`execute.sh`**; prefer **`run_all.sh`** for the setup + timed run + verification workflow described here. From the repository root:

```sh
cd evaluation/benchmarks
```

**Quick validation (recommended first):** easy mode, tiny inputs — typically tens of minutes including downloads:

```sh
bash run_all.sh --mode easy --size min --run-mode both
python3 show_results.py --size min
bash verify_outputs.sh --mode easy --size min
```

**Larger inputs:** easy mode, small inputs — often one to several hours wall time; use a generous disk (tens of GB free if retaining outputs):

```sh
bash run_all.sh --mode easy --size small --run-mode both --no-clear-outputs
python3 show_results.py --size small
bash verify_outputs.sh --mode easy --size small
```

`--no-clear-outputs` is required for `verify_outputs.sh` with `--size small` because the default otherwise deletes stdout files after each benchmark.

**Full 14-benchmark run** (requires extra setup for `dpt` and `image-annotation`; see per-benchmark READMEs and `setup.sh`):

```sh
bash run_all.sh --mode full --size small --run-mode both
```

**Results:** Timing tables are summarized from `evaluation/run_results/<size>/`. Optional: `python3 compare_to_baseline.py` if baselines are checked in.

**Methodology alignment with the paper:** Report speedup as Bash time divided by Incr time where applicable; repeat runs and average if matching the paper’s `XXX` runs per delta.

**Caveats:** Uses `sudo` for sandbox cleanup in some paths; writes under `/tmp`; runtime varies by machine (see hardware note elsewhere in this document).
```

### Checklist before submitting edited `INSTRUCTIONS.md`

- [ ] Re-execution section recommends **`run_all.sh`** as the primary driver; if legacy **`evaluation/benchmarks/run.sh`** / **`execute.sh`** are mentioned, label them **deprecated** and explain **`run_all.sh`** is the supported path.
- [ ] All **14** directory names appear if claiming full suite; **12** if describing only `--mode easy`.
- [ ] **`--no-clear-outputs`** is mentioned for **small** + **verify_outputs**.
- [ ] **`ptrace_scope`** and **`cargo build --release`** appear in prerequisites or a cross-reference to exercisability.
- [ ] Paper name mapping table or bullets included if the paper uses informal names (`dict`, `ngram`, …).

---

## What the suite measures

The suite runs real shell pipelines under **plain `bash`** and under **`incr`** (via [`incr.sh`](../incr.sh)), times each script, and optionally verifies that **stdout matches** between the two modes. Timing CSVs are aggregated under **`evaluation/run_results/<size>/`**.

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

Reserve **tens of GB** free if you retain all small outputs (inputs + stdout can be large; see [`EVALUATION.md`](EVALUATION.md) disk table).

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

**Harness behavior (stability):** [`run_lib.sh`](../evaluation/benchmarks/run_lib.sh) redirects **stdin from `/dev/null`** for both bash and incr (avoids hangs when stdin is a non-closing pipe). With `--run-mode both`, bash and incr run **interleaved per script** to avoid filling disk with huge bash-only stdout before incr runs. `TMPDIR=/tmp` during timed scripts; best-effort `/tmp` cleanup after each script.

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

- **Bash test suite equivalence:** [`evaluation/bash-ts/run.sh`](../evaluation/bash-ts/run.sh) — keep separate in `INSTRUCTIONS.md` (behavioral equivalence).
- **Single demo pipeline:** [`evaluation/war-and-peace/`](../evaluation/war-and-peace/) — exercisability / smoke test.
- **Legacy / paper scripts:** Cold-start and optimization plots may reference `evaluation/analysis/` or external `incr-paper` data; document those in their own subsections, not inside re-execution performance.

---

## Validation log (maintainers)

Example end-to-end check (easy mode):

1. Cleared easy-benchmark **`cache/`**, **`outputs/`**, **`inputs/`**, **`evaluation/run_results/`**, sentinels, and best-effort overlay/`/tmp` cleanup.
2. `cargo build --release`, `pip3 install -r requirements.txt`, `ptrace_scope=0`.
3. **`bash run_all.sh --mode easy --size min --run-mode both`** → 12 passed; **`verify_outputs.sh --mode easy --size min`** → OK (82 script pairs).
4. **`bash run_all.sh --mode easy --size small --run-mode both --no-clear-outputs`** → 12 passed; **`verify_outputs.sh --mode easy --size small`** → OK (82 script pairs).

Use as a template for a short “smoke test” paragraph in `INSTRUCTIONS.md` if desired.
