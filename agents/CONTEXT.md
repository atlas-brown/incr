# Incr Evaluation Suite Hardening — Agent Context

## Status: COMPLETE (as of 2026-04-08)

`run_all.sh` defaults to **easy + min**; explicit `--mode easy --size min` and `--size small` runs completed **12/12** on the dev machine after the fixes below. **`run_lib.sh` interleaves bash/incr per script when mode=both** so the disk is not filled by all bash stdout before incr runs (fixes ENOSPC on spell/unixfun/beginner-style workloads). During runs, **`TMPDIR=/tmp`** (sort temps and timing scratch). After **each** timed script it runs **`cleanup_tmp_artifacts`** (scrubs `/tmp` try/sort leftovers). For `--size small`, stdout files default to being cleared after each benchmark unless `--no-clear-outputs`.

**Harness:** `measure()` in `run_lib.sh` only prints **`[run] WARNING`** when a timed script exits with a code **other than 0 or 1** (POSIX tools such as `grep` use exit **1** for “no match,” which is normal). **`verify_outputs.sh`** (defaults **easy + min**, matching **`run_all.sh`**) diffs bash vs incr stdout and also fails if **htslib/samtools-style** missing-input / bad-index lines appear in `*.err` for benchmarks **other than `file-mod`** (ffmpeg writes banners to stderr there). Stdout agreement alone is not sufficient if both sides failed the same way.

**Spell:** `setup.sh` installs `wamerican` when `/usr/share/dict/words` is missing. `spell-6.sh` / `spell-7.sh` use `LC_ALL=C comm` with `sort -u` on the dictionary so `comm(1)` is satisfied (raw dict order is not `comm`-sorted). **Beginner:** `fetch.sh` uses `set -euo pipefail`, requires **~32GiB** free before downloading/preparing `--small` inputs, and runs merge/tripling **only** when creating `nginx-logs_small` (avoids doubling inputs on every setup). **`run_all.sh`** default per-benchmark timeout is **14400s** so `beginner` `--size small` does not hit `timeout` exit 124 under normal conditions.

## Task Summary
Prepared the `incr` evaluation suite for artifact evaluation at a top systems conference. Specifically:
1. Made `incr.sh` robust to SIGKILL via sentinel-based crash recovery
2. Created `setup.sh` (idempotent install+fetch) for all 14 benchmarks
3. Created `run.sh` (--mode/--size; shared `--scripts=` for per-script subsets via `run_lib.sh`) for all 14 benchmarks
4. Created min inputs for benchmarks that lacked them
5. Verified all 12 easy benchmarks end-to-end with min inputs; bash and incr outputs are identical
6. Created `evaluation/benchmarks/run_all.sh` with easy/full modes, global cleanup trap, result aggregation
7. Created `evaluation/benchmarks/show_results.py` to display results as a formatted table
8. Created `agents/EVALUATION.md` with detailed reviewer instructions
9. `compare_to_baseline.py`, `verify_outputs.sh`, `word-freq/scripts/gen_ips.py` + `gen_comm.py` for fetch.sh  
10. `evaluation/run_results/` is gitignored (generated locally; not committed)

**Commit policy:** Do not commit or push generated benchmark outputs/timing CSVs (`evaluation/run_results/`, per-benchmark `outputs/`) without the maintainer verifying runs on their machine. Agent runs may use a weaker model; treat artifacts as unreviewed until confirmed.

Root-level `.md` files were NOT modified. Scratch notes live in `agents/`.

## Key Files Changed/Created
- `incr.sh` — sentinel-based crash recovery
- `evaluation/benchmarks/run_lib.sh` — shared cleanup/timing helpers (sourced by all run.sh)
- `evaluation/benchmarks/run_all.sh` — global orchestrator
- `evaluation/benchmarks/show_results.py` — result display for artifact evaluators
- `evaluation/benchmarks/<name>/setup.sh` — idempotent install+fetch for all 14 benchmarks
- `evaluation/benchmarks/<name>/run.sh` — configurable timing wrapper for all 14 benchmarks
- `agents/EVALUATION.md` — reviewer-facing instructions
- `compare_to_baseline.py`, `verify_outputs.sh` — sanity checks

## incr.sh Robustness Fix
Single-file sentinel: the `.incr_orig` file IS the original script content (no separate /tmp backup).
1. Before overwriting: `cp "$script" "$sentinel"` — sentinel IS the backup
2. At startup: if sentinel exists from prior SIGKILL → restore script, remove sentinel, continue
3. In cleanup trap (EXIT/INT/TERM): restore from sentinel, remove it, remove sidecar
4. Child runs FOREGROUND — behaviorally identical to `bash script.sh`
   - SIGKILL: sentinel handles recovery on next run
   - SIGINT: process group receives it; child exits; deferred trap fires and restores
   - SIGTERM: deferred until child exits; trap fires and restores
   - Background (&+wait) was tried but POSIX sets SIGINT to SIG_IGN for async lists in non-interactive shells

## Known Environment Issue: stdin and benchmarks
**incr:** `incr` reads all of stdin before proceeding (stdin hash = part of cache key). In non-terminal environments (CI, IDE shell), stdin is often a pipe that never closes.

**Plain bash (measure):** Child processes such as **ffmpeg** (file-mod) may read stdin; if it is a blocking pipe, the first `ffmpeg` call can **hang** even though `incr` is not involved.

**Fix:** `run_lib.sh` `measure()` redirects **both** `incr` and `bash` invocations with `< /dev/null` (stdout/stderr captured as before). Benchmark scripts read inputs via env vars / paths, not stdin, so this is safe.

## Result File Layout
```
evaluation/run_results/
  <size>/
    <benchmark>-time.csv    # mode,script,time_sec rows
    <benchmark>-size.txt    # du -sb output for the incr cache
```
Both files land in the same size-specific subdir. `show_results.py` reads from there.

## Benchmark Classification

### Tier 1 — Easy (no special deps), run in easy mode
- beginner, bio, covid, file-mod, nginx-analysis, nlp-ngrams, nlp-uppercase, poet, spell, unixfun, weather, word-freq

### Tier 2 — Complex (excluded from easy mode)
- dpt: requires torch + segment-anything SAM model (~2GB download)
- image-annotation: requires OPENAI_API_KEY and `llm` CLI with gpt-4o-mini

## Min Inputs Created
| Benchmark    | What                                       | Where                           |
|--------------|--------------------------------------------|---------------------------------|
| beginner     | ~373 nginx log lines (valid combined format; includes `error` URLs for beginner-04–07) | min_inputs/nginx-logs/log0      |
| nlp-ngrams   | English text (~80 lines)                   | min_inputs/pg-min/sample.txt    |
| nlp-uppercase| same                                       | min_inputs/pg-min/sample.txt    |
| poet         | same                                       | min_inputs/pg-min/sample.txt    |
| spell        | same                                       | min_inputs/pg-min/sample.txt    |
| unixfun      | chess game notation                        | min_inputs/4.txt                |
| file-mod     | generated by setup.sh via ffmpeg           | inputs/songs.min/*.mp3          |
| word-freq    | fetch.sh --min downloads 1M.txt; setup.sh builds 10M.txt from it | inputs/10M.txt |
| bio          | `fetch.sh --min` wget **HG00421** from the **medium** URL, then by default **subsamples ~50% of reads** with `samtools view -s` (still a valid BAM; not byte truncation). Override with **`BIO_MIN_KEEP_FRAC=1`** for the full ~233 MB file. `input_min.txt` is `CHS HG00421`. | `inputs/bio-min/HG00421.bam` |

## Known Issues / TODOs for Future Agents
1. dpt and image-annotation not verified here (heavy deps)
2. word-freq `fetch.sh` re-downloads `1M.txt` when missing and regenerates IP/comm data each setup (acceptable)
3. spell `--size small` is slow; default `run_all` timeout is 14400s (4h)
4. After `--size small` with `--no-clear-outputs`, reserve tens of GB for stdout files

## Phase Status
- [x] Phase 0a: agents/CONTEXT.md initialized
- [x] Phase 0b: Manual incr exploration (wc, sort; cache structure confirmed)
- [x] Phase 0c: incr.sh sentinel-based kill recovery (single-file, foreground exec)
- [x] Phase 1a: Min inputs created for: beginner, nlp-ngrams, nlp-uppercase, poet, spell, unixfun
- [x] Phase 1b: setup.sh created for all 14 benchmarks
- [x] Phase 2: run.sh created for all 14 benchmarks (outputs/$RUN_SIZE isolation)
- [x] Phase 3a: 12/12 easy benchmarks PASSED with min inputs (bash + incr modes)
- [x] Phase 3b: 12/12 easy benchmarks PASSED with small inputs (bash + incr modes)
- [x] Phase 3c: bash==incr output verified for all 12 easy benchmarks (min inputs)
- [x] Phase 4: run_all.sh created (--clear-cache default on, --clear-outputs opt-in, --timeout 14400)
- [x] Phase 5: show_results.py created; result files consistently in run_results/<size>/
- [x] Phase 6: `bench` branch work squashed to a single commit vs `main` (see **Branch commit history** below)

## Branch commit history (`bench` vs `main`, chronological)

These were the individual commits before squash; they document how the evaluation work evolved. **Oldest first.**

1. **`8e4b5a2`** — *prompt* — Placeholder / scaffold.

2. **`d2cc790`** — *Add evaluation suite hardening: setup.sh, run.sh, min_inputs, robust incr.sh* — Sentinel-based SIGKILL recovery in `incr.sh`; `_run_lib.sh` helpers; idempotent `setup.sh` and configurable `run.sh` for all 14 benchmarks; min inputs for beginner, NLP, spell, unixfun; cleanup traps and `/tmp` scrubbing.

3. **`d12e670`** — *Add run_all.sh orchestrator, fix file-mod setup, update context* — Global `run_all.sh` (easy/full, sizes, run modes); file-mod uses ffmpeg only; `FAILED_SETUP` fix; context docs; initial min-run results.

4. **`ca95054`** — *fix(incr.sh): revert background exec* — Foreground child again (async `&` broke SIGINT in non-interactive bash); sentinel-only backup story documented.

5. **`52803b5`** — *fix(eval): correctness fixes, size-specific outputs, cache clearing* — Restore from sentinel correctly; `incr` stdin `</dev/null`; `outputs/$RUN_SIZE` everywhere; `run_all` cache/output flags and `FAILED_SETUP` order fix.

6. **`f920699`** — *fix(run_all): increase default timeout to 1800s, add --timeout flag* — Spell small needed longer than 600s; `--timeout=SECS` added.

7. **`b87514b`** — *docs(agents): update context with small-input verification results* — Documented 12/12 passes, sentinel design, stdin hang.

8. **`1f0b9d8`** — *refactor: clean up incr.sh and rename _run_lib.sh* — `run_lib.sh` naming; `measure()` rename; trim comments.

9. **`2902c1d`** — *fix(bio): use size-specific output dir* — Bio `OUT` under `outputs/$RUN_SIZE`; `run_all` help `--timeout=` form; removed stale run_results.

10. **`9c322bf`** — *feat(eval): add show_results.py* — Table of bash/incr times and cache sizes from `run_results/<size>/`.

11. **`d05fc13`** — *fix: put size.txt in same subdir as time.csv, add global cleanup trap* — `run_results/$SIZE/` for both artifacts; `show_results` path fix; INT/TERM trap restores sentinels globally.

12. **`dcf2c61`** — *style: remove underscore prefix from global_cleanup* — Naming only.

13. **`13a2a74`** — *test: verify bash==incr outputs…; increase default timeout to 7200s* — Output verification; default timeout 7200s.

14. **`22754da`** — *docs(agents): rename context.md to CONTEXT.md, add EVALUATION.md* — Reviewer-facing guide.

15. **`6fe136f`** — *feat(eval): add verify_outputs.sh* — Diff bash vs incr stdout for correctness checks.

16. **`2f93cc0`** — *docs: add disk space warnings for small inputs* — Documented large stdout; noted 12/12 small pass.

17. **`5743a09`** — *eval: baseline compare, verify robustness, TMPDIR for sort, small output defaults* — `compare_to_baseline.py`; `verify_outputs.sh` hardening; `run_lib` interleaved bash/incr, per-script `/tmp` cleanup; `run_all` default clear outputs for `--size small`; word-freq fetch helpers; gitignore updates.

18. **`ee6f28c`** — *chore: mark verify_outputs.sh executable*

19. **`9945079`** — *fix(eval): snake_case names; stop tracking run_results* — `cleanup`/`restore_tmpdir` naming; `evaluation/run_results/` gitignored; removed tracked artifacts.

20. **`99d49b3`** — *chore: restore executable bit on verify_outputs.sh*

21. **`07142b3`** — *fix(eval): spell dictionary and beginner fetch; shared run flags; longer default timeout* — Spell: `wamerican`, `spell-6/7` `comm` fix. Beginner: `fetch.sh` `set -e`, ~32 GiB preflight, merge/triple only on first create. Shared `parse_benchmark_run_sh_args` / `--scripts=`; `run_all --only=`; default timeout **14400s**; verified easy min + small 12/12.

After squash, this branch is a **single commit** on top of `main` containing the above work; this section preserves the narrative of the former sequence.
