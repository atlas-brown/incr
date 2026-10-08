# Minimum-input qualification results

All 96 benchmark entrypoints completed: 2,144 measurements. Bash, updated try/strace
and Observe each passed 536/536 runs. Pinned main passed 384 and failed 152:
146 required descendant cleanup and 29 had filesystem mismatches, with overlap.
Invalid baseline runs are excluded from speed comparisons.

Runtime sources are Incr `119e668` on `observe` and Observe `1817725` on `main`;
both were pushed before measurement. Pinned main is `4b8e5dd`. `final-build.json`
records full revisions, source/binary hashes, dependencies and input fingerprints.
`published-code.json` confirms the runtime sources and binaries remained unchanged.
`final-validation.json` records an independent completeness and raw-result audit.

## Correctness and code review

- All 24 fast-matrix groups passed, including 16 live/final policy and optimization
  configurations, chunking, shell transformation, strace, try, Observe and effect replay.
- All 83 Bash cases matched normalized native Bash test output (166 records).
- Observe passed 405 assertions. Incr passed 15 Rust tests; strict Clippy passed in
  both repositories before the frozen matrix.
- The early-write probes verified actual cache reuse after filesystem effects began.
  Selective restoration recovered unexpected preexisting speculative writes,
  including contents, mode and mtime, before installing cached final output.
- Runtime module review and consolidation are recorded in `../../CODE_REVIEW.md`.
  Shared capture/replay and bounded spooling replaced duplicate execution paths;
  obsolete parsers/caches were removed. Tracing, shell parsing, dependency keys,
  snapshot restoration and process cleanup received focused regression coverage.

These results qualify the tested inputs and contracts; they are not a proof that
arbitrary shell programs have no unhandled behavior.

## Performance

Speedup is reference time divided by Observe time. The reference below is updated
Incr using try/strace, without Observe.

| Scope | Cold geometric mean | Warm geometric mean | Cold sum of medians | Warm sum of medians |
|---|---:|---:|---:|---:|
| All 96 cases | 5.787x | 2.148x | 1.278x | 1.112x |
| 86 ordinary cases | 7.073x | 2.343x | 5.910x | 3.209x |
| 10 DPT variants | 1.031x | 1.019x | 1.031x | 1.019x |

File-modification warm runs improve 15.705x by geometric mean; word-frequency
improves 8.739x. DPT has no material warm-cache acceleration. Each DPT timing is a
single sample, so its small differences should not be treated as statistically
established speedups. Ordinary cases use three cold/warm pairs.

Observe is slower than updated try in two cold and six warm case medians. The worst
warm ratio is 0.951x (about 5.1% slower), with substantial sample variability.
On the 27 ordinary warm cases where pinned main is valid in every sample, Observe's
geometric mean ratio is 0.935x (about 7% slower). Plain Bash is faster overall on
these minimum inputs. `MEASUREMENTS.md` contains all reference comparisons;
`aggregate-timings.csv` preserves sample counts, medians and ranges.

## Assumptions and remaining limits

The benchmark policy is explicitly `--effect-policy final`: deterministic final
outputs matter, intermediate regular-file observations do not, and concurrent
external mutations are excluded. Candidates are validated before execution; all
writers stop before speculative restoration and cached-file installation. The
default `live` policy retains execution for shared-file/FIFO interactions and is
covered separately by the fast matrix. `../../OPTIMIZATIONS.md` maps each optional
optimization to its assumptions and tests.

Strict directory metadata dependencies can cause misses when code and changing
outputs share a directory. Weather plotting and DPT still perform substantial
work on warm runs. Ownership, explicit timestamp and unsupported special-file
operations retain replay barriers. Snapshot restoration is not a general concurrent
filesystem transaction. Failed restoration retains a recovery snapshot and errors.

Benchmark filesystem comparisons cover contents, modes, link targets/groups, empty
directories and deletions; they do not claim timestamp/ownership identity. Focused
regressions cover selected metadata and inode cases. Archives are compared by decoded
payload, and diagnostic normalization is documented in `MEASUREMENTS.md`.

Image annotation is excluded at the user's request. Full-size inputs are deferred.
Reusable dependencies, model downloads and frozen build snapshots are retained for
reproduction; disposable execution fixtures and caches are listed in `cleanup.json`.
