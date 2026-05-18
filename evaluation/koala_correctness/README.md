# koala_correctness

End-to-end correctness suite for `incr`. Each Koala benchmark is executed
twice — once under plain `bash` and once under `incr` — at a chosen input
size. Outputs are byte-for-byte diffed. A benchmark PASS means `incr` produces
identical results to unmodified `bash`.

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

Supported `--size` values: `min`, `small`, `full`. Each benchmark has
per-size timeouts; the harness also aggressively cleans up caches, overlays,
temp files, and incr sentinels after every benchmark and on SIGINT/SIGTERM.

## Benchmark status (--size=min)

| Benchmark   | Result | Scripts run | Dependencies | Notes |
|-------------|--------|-------------|--------------|-------|
| analytics   | **PASS** | `nginx`, `pcaps` | `jq`, `tcpdump` | Log-analysis pipelines; `pure_func` inlined (patch). |
| bio         | **PASS** | `bio` | `samtools`, `minimap2` | BAM processing; inner `cat \| while read` rewritten to `while read … done < file` (patch). |
| covid       | **PASS** | all | — | CSV analysis; no patches needed. |
| file-mod    | **PASS** | `compress_files`, `encrypt_files`, `img_convert`, `to_mp3`, `thumbnail_generation` | `ffmpeg`, `imagemagick`, `unrtf`, `zstd` | File format conversions; no patches needed. |
| nlp         | **PASS** | all | — | Text processing; `pure_func` inlined in all 6 scripts (patch). |
| oneliners   | **PASS** | `nfa-regex sort top-n wf spell sort-sort uniq-ips comm` | `dos2unix` | 8 of 11 scripts; 3 excluded (see below). |
| pkg         | **PASS** | `proginf` | `java` (JRE), mir-sa inputs | Static analysis of npm packages via mir-sa JAR; inputs fetched from atlas.cs.brown.edu. |
| unixfun     | **PASS** | scripts 1–21, 23–26, 28–36 | — | Unix utility pipelines; no patches needed. |
| weather     | **PASS** | `max-temp` | — | CSV max-temperature query; no patches needed. |
| ci-cd       | **SKIP** | — | — | Shell functions as commands + clang dependency (see below). |
| etcetera    | **SKIP** | — | — | Shell functions + mkfifo + FUSE dependency (see below). |
| web-search  | **SKIP** | — | — | Too slow at min + mkfifo in pipeline (see below). |

## Skipped scripts within otherwise-passing benchmarks

| Benchmark  | Skipped script(s) | Reason |
|------------|-------------------|--------|
| oneliners  | `diff`, `set-diff`, `bi-grams` | Use `mkfifo` + backgrounded readers/writers (incr limitation #4). |

## Skipped benchmarks

| Benchmark  | Reason |
|------------|--------|
| ci-cd      | Every makeself test script calls helper shell functions as bare top-level commands (`testDefault`, `testGzip`, `setUp`, …). incr's executor tries to `exec` those names as external binaries and fails (limitation #1). The `xz-clang` sub-benchmark additionally requires `clang`. |
| etcetera   | `sieve.sh` combines recursive shell functions (`primes`, `sequence`, `gen_composites`) with `mkfifo`+`&` fanout (limitations #1 and #4). `try.sh` needs `unionfs-fuse` / FUSE. |
| web-search | Two blockers: (1) the min dataset has 1000 Wikipedia articles and each spawns a fresh Node.js process (~3 s each, >50 min total); (2) `crawl.sh` and `combine.sh` both use `mkfifo` + backgrounded readers/writers (limitation #4). |
| rand       | `pass.sh` reads `/dev/urandom`; `pickname.sh` uses `shuf` — inherently non-deterministic across runs. |
| net        | Requires root and network namespaces. |
| ml / inference | Heavy ML dependencies (GPU, Ollama, external model files). |
| interact   | Interactive programs (game input, ohmyzsh installer) — not automatable deterministically. |
| repl       | `vps-audit` reads live system state (uptime, public IP); `git-workflow` modifies a git repo and needs a ~1 GB chromium dataset. |

## incr limitations found

During development, four categories of incr behavior that diverge from plain
bash were identified. Three required koala-script patches; one (mkfifo) is
handled by excluding the affected scripts.

| # | Limitation | Affected benchmarks / scripts | Resolution |
|---|-----------|-------------------------------|-----------|
| 1 | **Shell functions called as commands.** `insert.py` wraps every top-level command with `incr … cmd`. When `cmd` is a shell function (`export -f` or locally defined), `execvp(cmd, …)` fails — there is no binary named `cmd`. | `nlp/*` (`pure_func`), `analytics/nginx`, `analytics/pcaps` (`pure_func`), `ci-cd/makeself/test/*` (all test helper functions) | Inlined function body at each call site in the koala scripts (`nlp`, `analytics`). `ci-cd` is SKIP — the pattern is pervasive and non-trivially inlineable. |
| 2 | **Stdin drained for hashing inside `cmd \| while read; do <wrapped>; done` loops.** incr hashes stdin for each wrapped command; when a wrapped command sits inside the body of such a loop, it drains the pipe feeding the `read`, terminating the loop early. | `bio/bio.sh` (inner chromosome loop), `nlp/execute.sh` (fixed at harness boundary via `incr_shell.sh </dev/null`) | Rewrote inner loop in `bio.sh` to pre-compute the list into a variable and use `for chr in $chromosomes`. |
| 3 | **`{ s1; s2; … sN; } > file` group redirects.** `insert.py` wraps each statement as its own nested group but attaches `> file` only to the last one; `s1…s(N-1)` stdout goes nowhere. | `analytics/nginx.sh`, `analytics/pcaps.sh` | Replaced `{ … } > $f` with `: > $f` followed by `s1 >> $f; s2 >> $f; …`. |
| 4 | **`mkfifo` + backgrounded readers/writers hang.** incr's strace-based tracker cannot follow data through named pipes whose endpoints are in separate unrelated processes. | `oneliners/diff`, `oneliners/set-diff`, `oneliners/bi-grams`; `web-search/crawl.sh`; `web-search/combine.sh`; `etcetera/sieve.sh` | Excluded affected scripts; too invasive to rewrite without changing observable semantics. |

## Koala patches

The 9 patched koala scripts live in `koala_patches/` at the same relative
paths they occupy in the koala repo. The harness automatically applies them
before each run and reverts them on exit. See
[`koala_patches/README.md`](koala_patches/README.md) for the full rationale
and instructions for sharing the patches upstream.

```
koala_patches/
  analytics/scripts/nginx.sh
  analytics/scripts/pcaps.sh
  bio/scripts/bio.sh
  ci-cd/execute.sh           (kept for reference; ci-cd is currently SKIP)
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
    <benchmark>/            patched koala scripts (mirrored directory layout)
    apply.sh                apply / revert / check patches against a koala repo
    README.md               rationale for each patch
  work/                     runtime scratch (gitignored)
  results/                  per-run reports (gitignored)
```
