# Unannotated shell correctness qualification

Both complete, version-matched Bash suites pass on the current implementation:
the benchmark configuration matches installed Bash 5.1.16 in all 82 groups, and
the default configuration matches the verified Bash 5.2.37 build in all 83 groups.
Every group matches cold and warm. Static performance annotations are disabled.
Independent analysis recomputes comparisons from the retained raw captures.

| Check | Installed Bash 5.1.16 | Custom Bash 5.2.37 |
|---|---:|---:|
| Official corpus files verified | 625 | 668 |
| Matching groups, cold / warm | 82 / 82 | 83 / 83 |
| Matching transcript lines in each phase | 11,373 / 11,373 | 12,234 / 12,234 |
| Raw-exact groups including driver stderr, each phase | 73 | 73 |
| Timeouts / surviving descendants | 0 / 0 | 0 / 0 |
| Possible skip diagnostics | 0 | 0 |
| Native or Observe cold/warm output variations | 0 | 0 |
| Live / final focused regression exit status | 0 / 0 | 0 / 0 |
| Total qualification time | 749.776 s | 776.442 s |

The installed-shell run enables the native frontend, directory-access assumption
and content-validated workspace inputs used in the benchmarks (cache format 31,
Observe protocol 11); a preparation probe verifies native compilation
is accepted. The custom-shell run checks defaults, including Python compilation
and strict directory/file dependencies, with content-input validation disabled. Both use final effect policy through the
binary default, with INCR_EFFECT_POLICY unset. The custom shell intentionally
falls back from native compilation when it is not the supported installed target.

The native 5.1 run also matches its release's literal expected transcripts. Native
5.2 differs from literal expected output in builtins and execscript because of
host limits/trap presentation; Observe matches the native reference. A driver's
diff status of 1 alone is therefore distinguished from a differential failure.
All original source files, expected operands and driver statuses remain available.

## Evidence

- Installed-shell [summary](results/final-cleanup-system-bash-full-01/summary.json),
  [independent analysis](results/final-cleanup-system-bash-full-01/analysis.json),
  [case ledger](results/final-cleanup-system-bash-full-01/CASE_ANALYSIS.md).
- Defaults [summary](results/final-cleanup-defaults-full-02/summary.json),
  [independent analysis](results/final-cleanup-defaults-full-02/analysis.json),
  [case ledger](results/final-cleanup-defaults-full-02/CASE_ANALYSIS.md).
- [Current component records](results/final-cleanup-components/components.json):
  strict Clippy in both repos, 37 Incr Rust tests (one explicitly ignored), seven
  Observe units, 424 integration assertions, 11 AST tests and eight native-frontend
  tests. The unchanged shared harness passed 31 paper and seven supplemental tests;
  their original logs and source hashes are retained here. The Bash runner also
  executes 20 comparator/terminal checks before each complete suite.

Each result includes runtime source hashes, binaries, corpus metadata, setup logs,
raw stdout/stderr, captured diff operands, launcher coverage and cache inventories.
The suites perform 328 and 332 supervised group executions respectively. Cold
runs start from fresh fixtures/caches; each warm run retains only that cold run's
state. Groups have independent caches. Warm retained 378 and 391 metadata files
across 35 and 36 groups; this demonstrates retained state, not a hit for every
command. Source-sensitive and unsupported shell constructs may execute natively.
Shell equivalence alone is not evidence of acceleration.

## General fixes and comparison contract

Function inspection now preserves original source, including both printed bodies
and extdebug/declare-F locations. Compiler warnings or failure cause execution of
untouched source so the selected Bash diagnoses syntax itself. These are general
shell semantics fixes; installed command algorithms are unchanged.

Comparison normalizes only transformed source locations in diagnostics, diagnostic
line numbers, terminal process-group IDs, and PIDs in Bash signal diagnostics.
Signal descriptions, command text, arbitrary variable values and printed function
instrumentation remain compared. The previous type-specific prefix stripping was
removed, and a mutation test rejects observable wrapper text. Missing captures,
changed expected operands, abnormal status, timeouts and extra live descendants
remain failures. Tests use private /tmp and locales plus a controlling terminal.

One complete final-binary defaults trial had a native printf self-test cross a
one-second clock boundary. Native cold emitted four extra diagnostics; native
warm and both Observe phases matched expected output. That failed reference and
independent analysis remain in `results/final-cleanup-defaults-full-01`. A fresh
complete 83-group run passed, including printf cold/warm. The code, corpus and
comparison rules were unchanged; the failed run is not the current gate.

The earlier cross-version exploration used a Bash 5.2 corpus against installed
Bash 5.1: native jobs and quotearray varied between native runs, and native read
timed out. That evidence remains explicitly diagnostic. The runner now rejects
corpus/target major-minor mismatch. Earlier runs with prefix stripping and runs
stopped before the final source fixes are not the current correctness gate.
The historical results under results/upstream retain their original scope.

This qualifies the selected configurations and maintained suites. It does not
establish full benchmark performance; larger-input and real-model qualification,
checkpoint commits/pushes and full evaluations are tracked in the paper study.
