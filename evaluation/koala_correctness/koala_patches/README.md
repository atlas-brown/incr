# koala_patches

Behavior-preserving edits to a handful of Koala benchmark scripts that work
around `incr` limitations encountered while running the
`incr/evaluation/koala_correctness/` suite.

Each patched script lives at the same relative path it occupies in the Koala
repo — for example, `nlp/scripts/bigrams.sh` here corresponds to
`<koala>/nlp/scripts/bigrams.sh`. The harness (`run.sh`) applies these patches
to its target Koala checkout at the start of every run and reverts them on
exit; the originals are saved as `*.kc_orig` while the run is in flight. You
can also apply / revert / check them manually with `apply.sh`.

## Why these edits are needed

When `incr` instruments a Koala script via `src/scripts/insert.py`, each
top-level command is replaced with `<incr> <args> -- cmd ...`, and the wrapped
child is launched with `ShellCommand::new(prog).args(...)` (see
`src/command.rs`). That, plus how `incr`'s stream executor handles stdin and
pipelines, exposes several patterns in the upstream Koala scripts that are not
compatible with how `incr` runs them:

1. **User-defined shell functions used as commands.** Because the wrapped child
   is `execvp`'d directly (not run via `bash -c`), an `export -f pure_func` in
   the parent shell has no effect — the child looks for a binary named
   `pure_func` on `$PATH` and fails. Output silently becomes empty.
2. **Stdin draining inside `cmd | while read … ; do …; done` loops.** `incr`
   proactively reads and hashes stdin for each wrapped command. When a
   wrapped command sits inside the body of such a loop, it drains the pipe the
   loop is reading from, terminating the loop after one iteration. The harness
   already neutralizes this at the script-entry boundary via
   `incr_shell.sh </dev/null`, but inner-loop occurrences inside individual
   benchmark scripts still need editing.
3. **`{ s1; s2; … sN; } > file` brace-group redirects.** `insert.py` rewrites
   each statement inside the brace group as its own nested `{ … }` group but
   only attaches `> file` to the last one, so `s1..s(N-1)`'s stdout goes
   nowhere. Reproducible by running `insert.py` directly on a script that uses
   this pattern.
4. **`mkfifo` + backgrounded readers/writers.** `incr`'s strace-based
   dependency tracking can't follow data through named pipes whose endpoints
   are in unrelated processes; runs hang. The harness simply excludes the
   affected scripts rather than patching them, since the rewrite is too
   invasive to count as "slight".

## Patched files and which limitation each one addresses

### nlp / analytics / bio

| Patched file                                   | Limitation(s) | Edit summary                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `nlp/scripts/bigrams.sh`                       | (1)           | `pure_func` inlined into the `for input` loop body.                                                                                                                                                                                                                                                                |
| `nlp/scripts/bigrams_appear_twice.sh`          | (1)           | `pure_func` inlined (also fixes an upstream typo: `rm -rf {TEMPDIR}` → `rm -rf ${TEMPDIR}`).                                                                                                                                                                                                                       |
| `nlp/scripts/compare_exodus_genesis.sh`        | (1)           | `pure_func` inlined; uses `INPUT2` env var the script already sets.                                                                                                                                                                                                                                                |
| `nlp/scripts/count_trigrams.sh`                | (1)           | `pure_func` inlined.                                                                                                                                                                                                                                                                                               |
| `nlp/scripts/find_anagrams.sh`                 | (1)           | `pure_func` inlined.                                                                                                                                                                                                                                                                                               |
| `nlp/scripts/sort_words_by_num_of_syllables.sh`| (1)           | `pure_func` inlined.                                                                                                                                                                                                                                                                                               |
| `analytics/scripts/nginx.sh`                   | (1), (3)      | `pure_func` inlined. The eight pipelines that used to share a single `{ … } > $logname` group redirect now each write with `>> $logname` after an initial `: > $logname` truncate.                                                                                                                                  |
| `analytics/scripts/pcaps.sh`                   | (1), (3)      | Same shape of edit as `nginx.sh`: `pure_func` inlined, `{ … } > $logname` replaced with `: >` + `>>` appends. Also folds the now-redundant `egrep` invocations into `grep -E`.                                                                                                                                       |
| `bio/scripts/bio.sh`                           | (2)           | Outer `cat $IN_NAME \| while read s_line` rewritten as `while read … done < "$IN_NAME"`. Inner `cut … \| sort \| uniq \| while read chr` rewritten as `chromosomes=$(cut … \| sort -u)` plus `for chr in $chromosomes; do …`. Same observable output; no commands inside the inner loop have to consume stdin anymore. |

The `ci-cd` patch is purely additive (output capture only) and does not change any test logic. All other patches preserve the script's observable behavior under `bash` identically to the upstream version.

In every case the script's behavior under unmodified `bash` is identical to
the upstream version — the suite runs `bash mode` first and only marks a
benchmark `PASS` when the byte-for-byte diff against the `incr mode` snapshot
is empty.

## Excluded (not patched) for the same reasons

| Script                          | Reason                                                                                       |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| `etcetera/scripts/sieve.sh`     | Heavy use of recursive shell functions (`primes`, `sequence`, `gen_composites`, …) plus mkfifo+& fanout. Limitations (1) and (4) at once. |
| `etcetera/scripts/try.sh`       | Needs `unionfs-fuse` / FUSE.                                                                 |
| `oneliners/scripts/diff.sh`     | `mkfifo s1 s2` + two backgrounded writers. Limitation (4).                                   |
| `oneliners/scripts/set-diff.sh` | Same shape as `diff.sh`. Limitation (4).                                                     |
| `oneliners/scripts/bi-grams.sh` | Sources `bi-gram.aux.sh`, which defines `bigrams_aux` (limitation 1) and uses mkfifo+& internally (limitation 4). |
| `ci-cd/makeself/test/*`         | Every makeself test script defines helper functions (`testDefault`, `testGzip`, `setUp`, `tearDown`, …) and calls them as bare top-level commands. incr wraps those call sites and attempts to `exec` the function name as an external binary. The pattern is pervasive across all 11 test scripts and not fixable with a small patch. Limitation (1). |
| `ci-cd/riker/xz-clang`         | Requires `clang`, which is not installed.                                                     |

These are skipped by the per-benchmark runners under
`incr/evaluation/koala_correctness/benchmarks/`.

## Applying the patches to a koala repo

The harness handles this automatically, but you can also do it manually:

```bash
# Snapshot what will change:
./apply.sh --check  /path/to/koala
# Apply (saves <file>.kc_orig backups for any newly patched file):
./apply.sh --apply  /path/to/koala
# Revert (restores from <file>.kc_orig backups):
./apply.sh --revert /path/to/koala
```

All three subcommands are idempotent.

## Sharing back to upstream Koala

If you want to propose these edits to the upstream Koala maintainers as a real
PR (the harness exists precisely because this repository can't write to Koala
directly), the simplest path is:

```bash
# In a clone of koala that you can push from:
/path/to/incr/evaluation/koala_correctness/koala_patches/apply.sh \
    --apply "$(pwd)"

# Remove the .kc_orig backup files before committing — they are bookkeeping
# for the harness's revert step, not part of the patch.
find . -name '*.kc_orig' -delete

git add -A
git commit -m "Inline pure_func; avoid stdin-drained while-read loops; …"
```

Each edit is small enough to land independently if the maintainers prefer
that. The limitation rationale in the table above can be used verbatim in the
commit message / PR description.
