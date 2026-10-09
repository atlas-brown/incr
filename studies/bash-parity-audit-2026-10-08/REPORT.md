# Incr Observe: paper-aligned Bash correctness study

**Incr Observe matches native Bash on all 83 upstream groups, cold and warm: 12,234/12,234 transcript lines in each phase after the agreed trivial normalization.** The subset counted by the paper's artifact is **10,282/10,282** in each phase. There are no substantive mismatches, timeouts, surviving test descendants, cold/warm output changes, or detected missing-locale/terminal-skip diagnostics in the completed run.

This reproduces the behavioral-equivalence objective for the current Observe implementation and extends the accounting to every expected transcript. It is not a claim that the original paper's binary produced these new results, or that transcript lines are independent unit tests. No runtime code changed.

## Final results

| Check | Cold | Warm |
|---|---:|---:|
| Standard Bash groups matching native | 83/83 | 83/83 |
| Complete native transcript lines matching | 12,234/12,234 | 12,234/12,234 |
| Artifact-counted subset lines matching | 10,282/10,282 | 10,282/10,282 |
| Byte-exact groups, including driver stderr | 70/83 | 70/83 |
| Groups matching after presentation normalization | 13/83 | 13/83 |
| Cache entries after execution | 332 | 361 |
| Groups with cache entries | 31 | 31 |
| Unchanged metadata retained from cold | — | 331 files across 30 groups |
| Timeouts / surviving descendants | 0 / 0 | 0 / 0 |

The command completed in **783.25 seconds (13 minutes 3 seconds)**, including setup checks and regressions. All 332 native/Observe executions have retained records. Each phase has 84 real output captures; capability self-tests are excluded. The per-line ledger has 24,468 rows across both phases, all marked equal with matching normalized hashes. Cold and warm outputs are identical within each implementation under the same normalization.

The dedicated correctness suites also pass **57/57 live-policy tests** and **57/57 final-policy tests**, in 8.88 and 8.92 seconds. The harness passes **18/18 checks**, including negative comparisons, missing captures, exit-status changes, descendant handling, and terminal signal inheritance. The full-run logs are under `results/upstream/setup/`; the final expanded comparison/cleanup guards and full saved-evidence recheck are recorded in `results/verification.json`.

The only native differences against literal expected files are `builtins` (the environment permits a core limit of 0 rather than the expected 1000) and `execscript` (signal-trap display ordering). Observe matches native in both. The restored parser, empty/unset-PATH, locale, and terminal tests were not excluded. A nonzero literal-diff driver status caused solely by a reviewed presentation difference is preserved in the records and is not counted as a semantic failure.

The complete evidence is in [results/upstream/summary.json](results/upstream/summary.json), [case-results.csv](results/upstream/case-results.csv), [analysis.json](results/upstream/analysis.json), and [CASE_ANALYSIS.md](CASE_ANALYSIS.md).

## Process cleanup

All final executions triggered the supervisor's cleanup flag because the terminal/sudo arrangement left adopted descendants, usually already-exited zombies. Inspection of all retained process diagnostics found 8,408 zombie records and 24 sleeping-process records. Live background children occurred only in `assoc` and `redir`, with the same state/name counts in native and Observe, cold and warm. There were no Observe-only live-background cases and no survivors after cleanup. [lifecycle-analysis.json](results/upstream/lifecycle-analysis.json) records this distinction; a cleanup flag is not being reported as an Incr-specific leak.

## Reference methodology and counting

[Section 8.3 of the OSDI 2026 paper](https://www.usenix.org/system/files/osdi26-xie-yizheng.pdf) reports 10,279 matching ground-truth lines out of 10,282 across 83 categories. It uses native Bash as reference, notes 362 differences from bundled expectations, excludes 19 parser-error cases, and repeats with cache retained. Its remaining differences involve recursive aliases and an unset-PATH execution case.

This study adopts native differential comparison and retained-cache repetition. The verified GNU 5.2.37 archive contains 84 expected-output files with **12,234 LF-delimited lines**. The published denominator is now reconciled: the [archived artifact](https://zenodo.org/records/19488802) contains a counting script, `evaluation/bash-ts/categories.py`, which constructs `<category>.right` and skips missing files. Eight category names do not match their drivers' expected-file names; the nine omitted files contain 1,952 lines. Thus **12,234 − 1,952 = 10,282**, with all ten category totals matching the published table. This is an accounting omission, not evidence that the eight categories were unexecuted in the original evaluation.

[paper-accounting.json](paper-accounting.json) records the exact mapping, counts, and archived counting-script hash. The complete expected-file counts in the archive and official source agree; one archived expected file (`rsh.right`) differs in bytes from the official release, so this study deliberately verifies and executes the official source. Transcript lines are the scoring unit, not independently numbered assertions. Our full sweep includes every omitted transcript rather than reproducing the counting omission.

| Omitted category | Actual expected file(s) | Lines |
|---|---|---:|
| glob-test | glob.right | 261 |
| dollars | dollar.right | 744 |
| precedence | prec.right | 28 |
| exp-tests | exp.right | 419 |
| dirstack | dstack.right, dstack2.right | 79 |
| histexpand | histexp.right | 246 |
| input-test | input.right | 3 |
| execscript | exec.right | 172 |
| Total | 9 files | 1,952 |

## Why the initial evaluation was insufficient

The repository's vendored tests differ from the official sources in 16 top-level files. Several parser cases and the empty/unset-PATH checks were commented out; some direct script invocations were changed to use `THIS_SH`. The complete diff is [vendored-changes.diff](vendored-changes.diff). The official source also contains optional miscellaneous scripts absent from that vendored directory; these are outside standard `run-all` enumeration.

The initial suite therefore established parity on the edited corpus only. It also lacked a controlling terminal, and its first locale pass lacked several locales. Those results remain in `results/prior-evaluation.json.gz`, along with the main-branch samples and original regression evidence. They are not used for the final upstream score.

## Maintained test arrangement

The runner checks every official test-tree file against the downloaded GNU release hashes, builds current Incr/Observe, freezes the runtime, and uses Bash 5.2.37 plus its test helpers. Each group runs native cold/warm followed by Observe cold/warm, with the same cache and fixture retained between each implementation's two phases. Groups are isolated from each other. This is an immediate per-group repetition rather than two whole-suite passes sharing one global cache.

Original test sources and drivers are not patched. A native binary launcher supplies `THIS_SH`, preserves argv[0], and logs invocation arguments for coverage. Direct shebang invocations remain as specified by the official suite. The diff helper captures actual/expected operands and excludes self-comparisons used to probe diff features. All standard groups must produce matching capture counts and expected operands.

Every test has a controlling terminal; `read` additionally has terminal stdin. Private locale trees supply French, Japanese, Chinese, and German locales without modifying the host. Test processes run at the normal UID inside a private mount namespace and private `/tmp`. The terminal helper restores ordinary signal dispositions before exec. A preliminary helper bug propagated Python's ignored SIGPIPE/SIGXFSZ state; that partial run was interrupted, diagnosed, and superseded by a clean full run. Its focused evidence is retained in `results/terminal-helper-investigation.json.gz`.

Comparison preserves raw streams and exit statuses. It normalizes only diagnostic source paths/line numbers, terminal process-group IDs, and two reviewed executable prefixes in `type`'s displayed function. It does not discard parser-error cases, arbitrary diagnostics, changed command status values, missing captures, or output reordering. Literal driver diff status is considered separately from statuses printed by test programs. Lifecycle failures and Observe-only descendant cleanup fail the comparison.

## Limits on the conclusion

The target is Bash behavior under the tested live streaming configuration. Final-effect policy receives the focused regression suite, not another full Bash sweep. Batch/chunk execution, real-world benchmark performance, other Bash versions, and cross-group shared-cache interactions are not established by this study.

Original-source and invocation-mode fallbacks deliberately run some constructs natively. Cache counts and unchanged metadata show retained state but are not a universal command-hit count; focused regressions provide direct cache-reuse checks. Launcher coverage is an entry-point record, not full statement/branch instrumentation. Filesystem effects are assessed by the Bash scripts and dedicated regression tests, not by a complete before/after snapshot for every Bash case.

The evaluation cannot establish arbitrary nondeterministic, network-dependent, externally concurrent, or unsupported system behavior. It does establish whether each captured upstream transcript and driver stderr agrees under the documented comparison rules. The per-line ledger exposes both matching and mismatching reference/candidate line IDs without inventing test identifiers.

## Reproduction and evidence

Use [README.md](README.md) and `./studies/bash-parity-audit-2026-10-08/run.sh`. The maintained runner checks its own comparator/terminal helpers and writes raw compressed records, per-group JSON/CSV, setup/build/regression logs, progress, and provenance. [CASE_ANALYSIS.md](CASE_ANALYSIS.md) gives every group's purpose, output counts, statuses, cache retention, cleanup, source entry points, and baseline expected-file differences. The generated `line-results.csv.gz` is the exhaustive transcript-line ledger.

The initial architectural comparison with main remains in [DESIGN_COMPARISON.md](DESIGN_COMPARISON.md). Main's earlier sampled `execscript` execution had real missing-command status and repeated-startup-output differences; it was not used as the semantic oracle. No runtime source changes are part of this study.
