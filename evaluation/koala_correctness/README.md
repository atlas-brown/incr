# koala_correctness

End-to-end correctness suite for `incr`. Each Koala benchmark runs twice — under
plain `bash` and under `incr` — at a chosen input size. Outputs are diffed
byte-for-byte; a benchmark **PASS** means `incr` matches unmodified `bash`.

## Quick start

```bash
# Run all benchmarks at minimum input size (~2 minutes total)
bash run.sh --size=min

# Run a subset
bash run.sh --size=min --only=nlp,bio,analytics

# List available benchmarks
bash run.sh --list

# Install lightweight apt dependencies before running
bash run.sh --size=min --install-light
```

Supported `--size` values: `min`, `small`, `full`. Each benchmark has per-size
timeouts. The harness cleans up caches, overlays, temp files, and incr sentinels
after every benchmark and on SIGINT/SIGTERM.

## Benchmark status (--size=min)

| Benchmark | Result | Scripts run | Dependencies | Notes |
|-----------|--------|-------------|--------------|-------|
| analytics | **PASS** | `nginx`, `pcaps` | `jq`, `tcpdump` | Patched for #2b, #3. |
| bio | **PASS** | `bio` | `samtools`, `minimap2` | Patched for #2a. |
| covid | **PASS** | all | — | No patches. |
| file-mod | **PASS** | `compress_files`, `encrypt_files`, `img_convert`, `to_mp3`, `thumbnail_generation` | `ffmpeg`, `imagemagick`, `unrtf`, `zstd` | `pure_func` in `img_convert.sh` / `encrypt_files.sh` is exported and single-statement; works as-is. |
| nlp | **PASS** | all (incl. `trigram_rec`) | — | Six scripts patched for #2b. `trigram_rec.sh` has the same pattern but passes on `--min` because its grep filters match nothing. |
| oneliners | **PASS** | `nfa-regex sort top-n wf spell sort-sort uniq-ips comm` | `dos2unix` | 8 of 11 scripts; 3 excluded (below). |
| pkg | **PASS** | `proginf` | `java` (JRE), mir-sa inputs | Inputs from atlas.cs.brown.edu. |
| unixfun | **PASS** | scripts 1–21, 23–26, 28–36 | — | No patches. |
| weather | **PASS** | `max-temp` | — | No patches. |
| ci-cd | **SKIP** | — | — | #1; also needs `clang` for `xz-clang`. |
| etcetera | **SKIP** | — | — | #1 and #4; `try.sh` needs FUSE. |
| web-search | **SKIP** | — | — | Too slow at `min`; #1 and #4. |

## Skipped scripts (within passing benchmarks)

| Benchmark | Skipped script(s) | Reason |
|-----------|-------------------|--------|
| oneliners | `diff`, `set-diff`, `bi-grams` | `diff` / `set-diff`: #4. `bi-grams`: #1 (`bigrams_aux` not exported) and #4. |

## Skipped benchmarks

| Benchmark | Reason |
|-----------|--------|
| ci-cd | Makeself test scripts define helpers (`testDefault`, `testGzip`, …) locally and call them as commands. None are `export -f`'d, so incr tries to exec the name as a binary (#1). Could be fixed with `export -f`, but ~50 helpers across 11 scripts. `xz-clang` also needs `clang`. |
| etcetera | `sieve.sh`: un-exported helpers (#1) and `mkfifo` + `&` (#4). `try.sh`: needs `unionfs-fuse`. |
| web-search | `min` runs 1000 articles × ~3 s Node.js startup (>50 min). `crawl.sh` and `c/combine.sh`: #4; `combine.sh` also has local helpers (#1). |
| rand | `/dev/urandom` and `shuf` — non-deterministic. |
| net | Requires root and network namespaces. |
| ml / inference | GPU, Ollama, external model files. |
| interact | Interactive input; not automatable. |
| repl | Live system state; `git-workflow` needs ~1 GB chromium dataset. |

## incr limitations

Four behaviors where incr diverges from bash. Three are patched in koala scripts;
#4 is handled by excluding affected scripts.

| # | Limitation | Where it shows up | Fix |
|---|------------|-------------------|-----|
| **1** | **Local shell functions (no `export -f`).** `insert.py` wraps each call site as `incr funcname …`. Exported functions reach the child via `BASH_FUNC_funcname%%`; incr delegates them to `bash -c` (`skip_command` → `skip_executor`). Local helpers are invisible to the child, so incr tries to exec the name and fails (`strace: Can't stat 'funcname': …`). | `ci-cd/makeself/test/*`, `etcetera/sieve.sh`, `oneliners/bi-grams.sh`, `web-search/c/combine.sh` | SKIP (or add `export -f`). `nlp/*` and `analytics/*` use `export -f pure_func` — not affected by #1. |
| **2a** | **Stdin drain in `cmd \| while read` loops.** incr reads and hashes all stdin before launching the child, even when the child would not consume it. A wrapped command in the loop body drains the pipe after one iteration. | `bio/bio.sh` (inner loop). At script entry, `incr_shell.sh` redirects stdin from `/dev/null`. | Pre-compute the list; use `for` or `while read … done < file`. |
| **2b** | **Stdin drain inside exported functions.** Same mechanism, but inside an `export -f`'d function called with piped stdin. If the body runs a wrapped command (e.g. `mktemp`) before its first stdin read (`cat > file`), that command drains stdin and the read gets nothing. Function dispatch works; the body does not. Single-statement bodies (e.g. `file-mod/img_convert.sh`) are fine. | `nlp/*` (six patched scripts), `analytics/{nginx,pcaps}.sh`. `trigram_rec.sh` same pattern; passes on `--min` by accident. | Inline or restructure so the stdin consumer runs before any other wrapped command. |
| **3** | **Brace-group redirects `{ s1; s2; … } > file`.** `insert.py` nests each statement in its own `{ … }` but attaches `> file` only to the last; earlier stdout is lost. | `analytics/{nginx,pcaps}.sh` | `: > file` then `s1 >> file; s2 >> file; …` |
| **4** | **`mkfifo` + background readers/writers.** strace cannot track data through named pipes whose ends live in unrelated processes; the pipeline deadlocks. | `oneliners/{diff,set-diff,bi-grams}.sh`, `web-search/{crawl.sh,c/combine.sh}`, `etcetera/sieve.sh` | Exclude scripts. |

**Exported functions:** incr does support them. An earlier version of this doc
claimed all function calls fail under incr; that was wrong. `nlp/*` and
`analytics/*` needed patches for #2b (stdin drain inside the function body),
not for function dispatch.

## Koala patches

Nine patched scripts live in `koala_patches/` at the same paths as in the koala
repo. The harness applies them at run start and reverts on exit. See
[`koala_patches/README.md`](koala_patches/README.md) for per-file rationale.

```
koala_patches/
  analytics/scripts/nginx.sh
  analytics/scripts/pcaps.sh
  bio/scripts/bio.sh
  ci-cd/execute.sh           (reference only; ci-cd is SKIP)
  nlp/scripts/bigrams.sh
  nlp/scripts/bigrams_appear_twice.sh
  nlp/scripts/compare_exodus_genesis.sh
  nlp/scripts/count_trigrams.sh
  nlp/scripts/find_anagrams.sh
  nlp/scripts/sort_words_by_num_of_syllables.sh
  apply.sh
  README.md
```

## Directory layout

```
koala_correctness/
  run.sh                    entry point
  lib.sh                    shared helpers (cleanup, fetch, diff, …)
  incr_shell.sh             KOALA_SHELL wrapper that invokes incr.sh
  benchmarks/
    <name>/run.sh           per-benchmark configuration
  koala_patches/
    <benchmark>/            patched koala scripts (mirrored layout)
    apply.sh                apply / revert / check patches
    README.md               per-patch rationale
  work/                     runtime scratch (gitignored)
  results/                  per-run reports (gitignored)
```
