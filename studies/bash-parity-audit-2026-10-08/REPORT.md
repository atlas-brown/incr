# Incr Observe: clean final-policy Bash correctness study

**The default effect policy is now final, and the clean full upstream Bash suite matches native Bash in all 83 groups, cold and warm.** All 12,234/12,234 transcript lines match in each phase after the agreed trivial normalization. The paper-counted subset also matches: 10,282/10,282 per phase, compared with the paper's reported 10,279/10,282.

## Verified results

| Check | Cold | Warm |
|---|---:|---:|
| Groups matching native | 83/83 | 83/83 |
| Complete transcript lines matching | 12,234/12,234 | 12,234/12,234 |
| Paper-counted subset matching | 10,282/10,282 | 10,282/10,282 |
| Byte-exact groups including driver stderr | 70/83 | 70/83 |
| Groups requiring trivial normalization | 13/83 | 13/83 |
| Cache entries | 405 | 476 |
| Groups with cache entries | 41 | 41 |
| Unchanged metadata retained from cold | — | 378 files across 36 groups |
| Timeouts / surviving descendants | 0 / 0 | 0 / 0 |

The run completed in **815.56 seconds (13 minutes 36 seconds)** including clean Rust builds, setup and focused regressions. All 332 executions have new raw records. Each phase captures 84 actual transcripts, excluding diff capability self-comparisons. The regenerated line ledger contains 24,468 equal rows. There are no cold/warm output changes or detected missing-locale/terminal-skip diagnostics.

The focused suites pass **57/57 under live** and **57/57 under final**. All **18 harness checks** and **29 Rust tests** pass, including the normally ignored ownership test run explicitly with the available noninteractive sudo. The runtime change is the one-line binary policy default; there were no additional runtime correctness fixes needed for this result. Earlier live-policy and exploratory Bash artifacts were removed; git commit `4a772a4` retains them.

Native differs from literal upstream expected files only in `builtins` (host core limit) and `execscript` (trap display ordering). Observe matches native for both. Literal driver diff status 1 caused by accepted presentation differences is retained in records and distinguished from command statuses printed by the tests.

The supervisor diagnostics contain 8,390 exited-zombie and 24 sleeping-process records. Live background children occur only in `assoc` and `redir`, with matching native/Observe names and counts. Those flags are not being reported as Observe-only leaks: native and Observe lifecycle comparisons pass, and no children survive bounded cleanup. The comparison checks live process names/counts separately from zombies.

See [summary.json](results/upstream/summary.json), [analysis.json](results/upstream/analysis.json), and [CASE_ANALYSIS.md](CASE_ANALYSIS.md) for the complete results.

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

## Execution and scope

The runner exercises the actual binary default with INCR_EFFECT_POLICY unset. Both Rust target directories and frozen runtime snapshots were removed before rebuilding. Every cold run starts with an empty private cache and fixture; warm retains only its corresponding new cold state. All 668 official Bash test-tree files are verified against GNU Bash 5.2.37. Parser prerequisites and the pinned Bash build are reused, not previous results or caches.

The suite runs all 83 standard groups, native and Observe, cold and warm: 332 executions. Original sources and drivers are unmodified. Each test has a controlling terminal, required locales, private /tmp and bounded child supervision. The runner compares captured output and driver stderr, accepting only reviewed source-location, line-number, process-group-ID and executable-prefix differences. Missing captures, substantive output changes, timeouts and surviving descendants fail.

## Why Observe passes the historical problem cases

The relevant fixes live in the shell wrapper and AST transformer on the Observe branch, not in ptrace alias handling. Alias/function bindings remain under Bash's control; dynamic alias names preserve original source. Builtins such as command remain native, unknown commands retain Bash lookup and exit status, and wrapper helpers use command -p even when PATH is empty or unset. Syntax-invalid files are passed unchanged to Bash for its own diagnostic and status. Source-sensitive constructs and invocation modes also use native execution. See [DESIGN_COMPARISON.md](DESIGN_COMPARISON.md) for the implementation explanation.

Changing to final does not alter those shell rules. It allows validated filesystem output replay after speculative effects, assuming final outputs are the desired contract. Use INCR_EFFECT_POLICY=live when intermediate regular-file observations matter. FIFO dependencies still block reuse.

## Limits and reproduction

Transcript lines are not independent unit tests. Native fallbacks are part of correctness, not evidence that every construct is accelerated. Cache retention is not a universal cache-hit count. Final-output parity does not establish arbitrary concurrent interaction equivalence, nondeterministic/network-dependent behavior, batch/chunk performance or other Bash versions. This run repeats each group immediately with a retained cache; it does not use one cache across two whole-suite passes. Optional tests/misc scripts are outside the standard run-all corpus.

Use [README.md](README.md) and ./studies/bash-parity-audit-2026-10-08/run.sh. [CASE_ANALYSIS.md](CASE_ANALYSIS.md) was regenerated and independently rechecked from all new raw records. The complete evidence is retained under results/upstream. Historical qualification documents are dated development records; this report describes the current default and current Bash evaluation.
