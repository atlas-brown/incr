# koala_patches

Behavior-preserving edits to Koala benchmark scripts that work around incr
limitations found by the [`koala_correctness`](../README.md) suite.

Each file here mirrors its path in the koala repo (e.g. `nlp/scripts/bigrams.sh`
→ `<koala>/nlp/scripts/bigrams.sh`). The harness applies patches at run start
and reverts on exit, saving originals as `*.kc_orig`. Use `apply.sh` to apply,
revert, or check manually.

Limitation numbers match [`../README.md`](../README.md).

## Background

`insert.py` wraps top-level commands as `<incr> … -- cmd …`. The wrapped child
runs through incr's stream executor, which always reads stdin before launch.
That, plus how brace groups are rewritten, drives the patches below.

**Important:** `pure_func` in `nlp/*` and `analytics/*` is `export -f`'d. incr
detects it via `BASH_FUNC_pure_func%%` and runs it through `bash -c` — function
dispatch is not the problem. Those scripts failed because a wrapped command
inside the body (typically `mktemp`) drained piped stdin before `cat > file`
could read it (#2b). Inlining fixes that by restructuring the pipeline.

## Patched files

| File | Limitation | Change |
|------|------------|--------|
| `nlp/scripts/bigrams.sh` | #2b | Inline `pure_func`; first stage writes to a file before other wrapped commands. |
| `nlp/scripts/bigrams_appear_twice.sh` | #2b | Same; also fixes `rm -rf {TEMPDIR}` → `rm -rf ${TEMPDIR}`. |
| `nlp/scripts/compare_exodus_genesis.sh` | #2b | Inline `pure_func`. |
| `nlp/scripts/count_trigrams.sh` | #2b | Inline `pure_func`. |
| `nlp/scripts/find_anagrams.sh` | #2b | Inline `pure_func`. |
| `nlp/scripts/sort_words_by_num_of_syllables.sh` | #2b | Inline `pure_func`. |
| `analytics/scripts/nginx.sh` | #2b, #3 | Inline `pure_func`; `cp` replaces piped stdin. Replace `{ … } > file` with `: >` + `>>`. |
| `analytics/scripts/pcaps.sh` | #2b, #3 | Same as `nginx.sh`; `egrep` → `grep -E`. |
| `bio/scripts/bio.sh` | #2a | `while read … done < file` and `for chr in $chromosomes` instead of piped `while read` loops. |

The `ci-cd/execute.sh` patch only adds output capture; it does not change test
logic. All patches preserve bash behavior; the suite runs bash first and only
marks **PASS** when incr output matches byte-for-byte.

## Excluded (not patched)

| Script | Reason |
|--------|--------|
| `etcetera/scripts/sieve.sh` | #1 (un-exported helpers) + #4 |
| `etcetera/scripts/try.sh` | FUSE dependency |
| `oneliners/scripts/diff.sh`, `set-diff.sh` | #4 |
| `oneliners/scripts/bi-grams.sh` | #1 + #4 |
| `ci-cd/makeself/test/*` | #1 (~50 local helpers) |
| `ci-cd/riker/xz-clang` | needs `clang` |
| `web-search/scripts/crawl.sh`, `c/combine.sh` | #4; `combine.sh` also #1 |

These are SKIP'd by runners under `benchmarks/`.

## Manual apply / revert

```bash
./apply.sh --check  /path/to/koala   # preview
./apply.sh --apply  /path/to/koala   # patch (saves *.kc_orig)
./apply.sh --revert /path/to/koala   # restore
```

All three are idempotent.

## Sharing upstream

```bash
/path/to/incr/evaluation/koala_correctness/koala_patches/apply.sh --apply "$(pwd)"
find . -name '*.kc_orig' -delete
git add -A
git commit -m "Inline pure_func; avoid stdin-drained while-read loops; …"
```

Each edit is small enough to land independently.
