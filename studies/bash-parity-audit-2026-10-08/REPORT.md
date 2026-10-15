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
| Total qualification time | 750.769 s | 773.150 s |

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

- Installed-shell [summary](results/content-inputs-system-bash-full-01/summary.json),
  [independent analysis](results/content-inputs-system-bash-full-01/analysis.json),
  [case ledger](results/content-inputs-system-bash-full-01/CASE_ANALYSIS.md).
- Defaults [summary](results/content-inputs-defaults-full-01/summary.json),
  [independent analysis](results/content-inputs-defaults-full-01/analysis.json),
  [case ledger](results/content-inputs-defaults-full-01/CASE_ANALYSIS.md).
- [Current component records](results/content-inputs-components/components.json):
  37 Rust tests (one explicitly ignored), seven Observe units, 424 integration
  assertions and the content-input replacement regression. The serial queue
  also passed [31 paper tests](../paper-size-benchmarks/results/content-inputs-qualification-02/paper-harness-tests.log)
  and [seven supplemental tests](../paper-size-benchmarks/results/content-inputs-qualification-02/supplemental-harness-tests.log).
  The Bash runner executes 20 comparator/terminal checks before each full suite.
  Earlier AST/native-frontend component records remain historical evidence in
  `results/final-source-components/`; final checkpoint component refresh is pending.

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

The earlier cross-version exploration used a Bash 5.2 corpus against installed
Bash 5.1: native jobs and quotearray varied between native runs, and native read
timed out. That evidence remains explicitly diagnostic. The runner now rejects
corpus/target major-minor mismatch. Earlier runs with prefix stripping and runs
stopped before the final source fixes are not the current correctness gate.
The historical results under results/upstream retain their original scope.

This qualifies the selected configurations and maintained suites. It does not
establish full benchmark performance; larger-input and real-model qualification,
checkpoint commits/pushes and full evaluations are tracked in the paper study.
