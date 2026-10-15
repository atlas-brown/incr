# Historical-size benchmark study

This study measures corrected benchmark programs under native Bash, pinned
original Incr (`4b8e5dd` plus the reviewed minimal fix below), and current Incr
with Observe (`final` policy). All modes execute identical benchmark source.
Image annotation is excluded because it requires an API key. Web search and
Tufte weather are outside this paper matrix.

See [CHANGE_AUDIT.md](CHANGE_AUDIT.md) for intentional workload repairs and
historical input ambiguities. These measurements reproduce the incremental
development experiment with corrected workloads and recorded dataset recipes;
they do not claim byte-identical reproduction of missing historical input files.
Historical fetch recipes and recorded timings take priority over potentially stale
paper size descriptions. `paper` is the CLI name for this historical-size profile.

## Current checkpoint status

Read [ACTIVE_GOAL_HANDOFF.md](ACTIVE_GOAL_HANDOFF.md) first for the current state.
The implementation now excludes the experimental byte-sort replacement and cut
annotation, following the requirement to optimize general execution mechanisms.
Earlier minimum/scaled speedups used those specializations and must not qualify
this revised source. Correctness and performance need fresh qualification,
including DPT. The full evaluation is incomplete; no all-benchmark speedup is
established. Non-paper workloads need separate coverage for the broader goal.

## Modular workflow

Run from the Incr repository root. Each command performs only its named stage.
Nothing automatically promotes a minimum run into a paper-size evaluation.

```bash
# Check installed dependencies and rebuild all three release binaries serially.
bash studies/paper-size-benchmarks/run.sh doctor --build

# Prepare tiny inputs; inspect results before selecting larger inputs.
bash studies/paper-size-benchmarks/run.sh prepare --profile min
bash studies/paper-size-benchmarks/run.sh run --profile min \
  --only file-mod,word-freq --repetitions 1 --run-id min-pilot

# Explicitly launch remaining minimum measurements in the background.
python3 studies/paper-size-benchmarks/harness/launch.py --profile min \
  --only nlp-ngrams,nlp-uppercase,covid,weather,nginx-analysis,beginner,unixfun,poet,dpt,spell,bio \
  --repetitions 1 --run-id min-matrix

# After inspecting the corresponding minimum results, prepare a family explicitly.
bash studies/paper-size-benchmarks/run.sh prepare --profile paper --only file-mod
python3 studies/paper-size-benchmarks/harness/launch.py --profile paper \
  --only file-mod --repetitions 3 --run-id paper-music-01 --release-inputs
```

For a persistent preparation-only job, use `launch.py --stage prepare --profile
paper --only <families> --run-id <unique-id>`. Inspect its `status.json` and saved
input inventories; then explicitly launch a separate measurement job. No stage
launches the next stage automatically.

Choose a new run ID for each independent evaluation. `--only` accepts comma-
separated families; execution order always follows `manifest.json`, from smaller
historical expected inputs to larger ones. Actual prepared sizes are recorded. Each repetition resets the fixture and starts with
an empty cache. The cache remains across that family's ordered script versions.
An interrupted sequence is restarted from empty state, preserving the failed
attempt under a separate directory. Completed sequences can be resumed:

```bash
bash studies/paper-size-benchmarks/run.sh run --profile paper --only file-mod \
  --repetitions 3 --resume studies/paper-size-benchmarks/results/paper-music-01
```

Resume requires the original configuration, manifest, harness, and frozen build.
For background jobs the launching harness is copied into `.work/jobs/<run-id>`;
that copy can be used with `INCR_BENCH_STUDY` set to the absolute study path when
resuming after repository edits. No completed evidence is overwritten.

## Persistence and inspection

`launch.py` starts `incr-bench-study.service` in the user systemd manager and
enables lingering for the current user so closing the window or logging out does
not end it. It runs one explicitly selected evaluation, with no automatic restart
and no automatic setup. The service and runner reject overlapping evaluations.

```bash
systemctl --user status incr-bench-study.service
tail -n 40 studies/paper-size-benchmarks/results/logs/paper-music-01.log
bash studies/paper-size-benchmarks/run.sh status \
  studies/paper-size-benchmarks/results/paper-music-01
bash studies/paper-size-benchmarks/run.sh report \
  studies/paper-size-benchmarks/results/paper-music-01

# Stop the owned service and its complete process group.
systemctl --user stop incr-bench-study.service
```

`status.json` contains the current family, script, mode, repetition, PID, elapsed
time, disk usage and last update. Finished/failed state is written explicitly.
The log is retained after systemd releases the transient service.

## Correctness and measurement

Every script version is compared against its repetition's native Bash result.
The runner compares status, exact stdout hashes, narrowly normalized stderr,
application filesystem contents/modes/link relationships, and workload-specific
checks. BAMs are quickchecked and compared as decoded alignments/headers excluding
`@PG` command provenance. Encrypted/compressed archives are compared by decoded
members and payloads. DPT uses the real models and verifies classifications and
the final stage’s PNG output; changed working images are compared too.

Validation has its own 600-second process-tree deadline. It runs outside timing.
Private TMPDIR contents are measured and removed separately; they are not
application outputs. Required immutable input/source inventories are checked.
Unexpected errors, timeouts, surviving live descendants, missing artifacts and
output mismatches invalidate a sample. Zombies adopted after speculative
cancellation are recorded and reaped. Failures never become speedups. The default
stops at the first failed sequence; `--continue-on-failure` collects diagnostic
coverage while keeping the report incomplete.

GNU `time` records CPU time, RSS, faults, context switches and filesystem I/O.
Its inherited output descriptor is closed by the tiny native `fdguard` launcher
before the top-level shell starts. Otherwise Incr correctly bypasses caching.
All modes use the same guard; intentional descriptors opened by the benchmark
shell remain intact. Observe sequences with no cache entries fail an
instrumentation check. Entry retention is evidence of retained cache metadata,
not a universal cache-hit count.

Bash references run first in each repetition. Original/Observe order alternates
between repetitions. Runtimes, shell helpers, benchmark sources and validation
code are frozen per run. Thread counts, locale, package versions, input hashes,
environment and source revisions are recorded. Cold means an empty Incr cache,
not a flushed operating-system page cache. No other benchmark job runs in parallel.

## Disk lifecycle

The default reserve is 8 GiB; the disposable workspace budget is 32 GiB.
Measurements check free disk space every second and sample allocated workspace/
cache usage every ten seconds. Peak usage is sampled, not an exact instantaneous
maximum. Download/extraction also checks space and avoids keeping the full NLP or
weather archive when selecting smaller inputs.

Each sequence measures cache size before deleting it. Large captures are hashed,
validated and removed after each version; a failing capture retains its first
MiB for diagnosis. Working outputs stay across versions, then are removed with
the cache. `--release-inputs` removes that family's prepared dataset after all
requested repetitions/modes finish. Models and the existing dependency environment
are reused. Cleanup touches only owned `.work` children; it unmounts only mounts
under those paths and refuses deletion while any remain. Global `/tmp` is never
purged.

## Evidence and statistics

Each `results/<run-id>` holds configuration/environment/build snapshots, complete
input inventories, Bash references, one JSON per invocation, sequence completion
markers, durable events, `timings.csv`, `summary.json`, and `report.md`. Records
include wall/CPU time, RSS, I/O, faults/switches, output hashes, filesystem manifests,
cache entries retained/changed, final/peak sampled cache and workspace bytes,
private temporary bytes, descendant states, validity and diagnostics.

Reporting requires every scheduled mode/version/repetition before claiming a
complete study. It computes means, medians, sample standard deviations and ranges,
plus per-edit Observe ratios against Bash and original Incr. Historical-size
reports include current/historical timing factors and flag differences outside
0.5–2× for investigation; intentional workload changes are contextualized in the audit. The cold initial
version is excluded from edit-speedup aggregates. Raw samples remain available.
`reference/historical-timings.csv` retains the three historical paper repetitions.

## Harness fault checks

```bash
python3 studies/paper-size-benchmarks/harness/test_harness.py -v
```

Run these checks before measurements, serially. They inject hangs, detached
children, disk exhaustion, output corruption, late errors, unsafe archive paths,
cleanup escapes and lock contention. Do not run tests/builds during measurements.

## Verified minimum evidence

[MIN_VALIDATION.json](MIN_VALIDATION.json) identifies the manually reviewed
sequences covering all 13 families, 92 versions and all three modes: 276 valid
invocations. `min-repeat-01` additionally validates two independent repetitions
and a completed resume that performs no measurements. Earlier incomplete attempts
are retained for diagnosis and excluded from this qualification ledger.

Saved reports can be plotted independently using the installed environment:

```bash
qualification/.venv/bin/python studies/paper-size-benchmarks/harness/plots.py \
  studies/paper-size-benchmarks/results/<run-id>
```

Figures are standalone PNG/PDF artifacts. Plot/report commands never execute benchmarks.

## Current historical-size evaluation

Full preparation was explicitly launched as `historical-inputs-01`, completed,
and inspected in [FULL_INPUT_REVIEW.json](FULL_INPUT_REVIEW.json). Measurement was
then explicitly launched as `historical-eval-02`: 92 versions across 13 families,
three modes and three repetitions, totaling 828 scheduled invocations.

```bash
bash studies/paper-size-benchmarks/run.sh status \
  studies/paper-size-benchmarks/results/historical-eval-02
tail -n 30 studies/paper-size-benchmarks/results/logs/historical-eval-02.log
```

The persistent service records progress and enforces deadlines/disk limits. A
correctness failure stops its sequence and preserves evidence for inspection;
this explicitly selected `--continue-on-failure` run then collects other sequences.
Completed families release their prepared inputs; each sequence releases its
measured runtime cache and fixture. Reports update after each sequence; a partial
report is explicitly incomplete. No claim of all scheduled results is made until
`status.json` says complete and `summary.json` confirms every sample is valid.

`historical-eval-01` stopped on the reproduced original-Incr encrypted-output
failure described in the audit. `full-music-diagnostic-01` retains the targeted
rerun. The replacement evaluation excludes invalid samples and retains failed
family inputs, while collecting valid measurements elsewhere.

## Five-minute monitor

`incr-bench-monitor.timer` runs a low-priority, read-only audit every five minutes.
It checks heartbeat/service health, free disk, resource fields, validation flags,
and saved output/stdout/stderr comparisons against each repetition's Bash
reference. Actual output decoding remains part of every invocation's bounded
validator, before outputs are removed. The monitor records known failures rather
than suppressing them, and does not restart or alter measurements.

Latest audit: `results/historical-eval-02/monitor.json`; append-only history:
`monitor-history.jsonl`. The timer persists after logout. It does not wake an
interactive chat agent or send external notifications.

```bash
systemctl --user list-timers incr-bench-monitor.timer
journalctl --user -u incr-bench-monitor.service -n 30
systemctl --user stop incr-bench-monitor.timer
```

## Baseline repair and timing update

After the user authorized minor baseline bug fixes, `original-minimal-fixes.patch`
was applied to original Incr: `openssl enc` executes fresh because random salted
ciphertext cannot combine live speculative prefixes with older cached suffixes.
The same guard applies to the candidate. Following the user’s fairness clarification,
the patch also gates original Incr’s static pure/read-only/stateless tracing shortcuts
on its existing `-a` option. Both implementations now disable these static annotations
by default; learned introspection is retained. Evaluate the unannotated configuration
first; an equally annotated comparison is deferred. The study records `annotations: false`.
Earlier ratios with unequal static annotation coverage are diagnostic only.
Doctor accepts only this exact reviewed patch and records it with source fingerprints. Earlier `historical-eval-*` results
used the untouched baseline; `optimization-min-*` use the repaired baseline.

Fresh measurement timing records child completion with a waiter thread, excluding
initial workspace inventory and polling delay. Earlier results retain their
original measurement semantics and are not silently rewritten as fresh evidence.
The interrupted full evaluation and periodic monitor are stopped while runtime
optimization continues. See the performance regression study for current work.


## Explicit cleanup before a fresh evaluation

After the study service terminates, inspect and apply a cleanup plan as a separate
stage. This takes the same nonblocking study lock as measurements. It includes
both legacy artifact locations and the isolated `.work/runner` layout; recovery
snapshots prevent cleanup until inspected. Result JSON/CSV, source archives,
reference results, minimum inputs, immutable model weights and frozen jobs remain.

```bash
python3 studies/paper-size-benchmarks/harness/cleanup.py --include-inputs
python3 studies/paper-size-benchmarks/harness/cleanup.py --include-inputs --apply
```

`--include-inputs` removes prepared historical-size inputs and download files, so
prepare those inputs explicitly again before measuring. Repeat `--build OLD_ID`
to remove explicitly selected obsolete frozen builds; retain reference builds
needed for paired regression probes. Each applied cleanup writes durable evidence
under `results/maintenance`, including partial failures and free space before/after.
This does not clear machine-wide kernel or package caches. It resets the study's
memoization and working artifacts; each measured mode/repetition additionally
starts with a fresh application cache and keeps it across its version sequence.
