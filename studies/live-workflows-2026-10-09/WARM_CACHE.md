# Retained-cache and Bash execution audit

This audit extends the original [cold-run report](REPORT.md). It compares native
Bash, regular Incr, and Incr with Observe, and distinguishes retained cache state
from demonstrated replay. Live interactions and final-output reuse are different
contracts; passing one does not establish the other.

## Result: ordinary checks pass, but lock-sensitive warm replay is incorrect

**This audit does not give general warm-cache correctness an all-clear.** The
original sixteen workflows continue to match their expected outcomes with caches
retained. The ordinary Bash and input-invalidation checks also pass. A separate
changed-lock-state probe, however, finds that Observe can replay a cached `busy`
answer after the lock has been released.

| Check | Result |
|---|---|
| Official Bash corpus, Observe versus native, default final policy | 83/83 cold and 83/83 warm groups match; 332 executions. |
| Original live scenarios, three backends, five phases | 240/240 expected outcomes, including the predicted regular-Incr isolation failures. |
| Twelve Bash-wrapper programs, three backends, two policies, six phases | 432/432 native-equivalent outcomes. |
| Corrected explicit batch replay/invalidation probes | 48/48 outcomes; 18 confirmed hits with no worker launch. |
| Original live scenarios under exploratory final policy | 240/240 expected outcomes; this does not extend the final-policy contract. |
| Sequential infrastructure controls across these three audit invocations | 9/9 pass. |
| Focused regressions, eight execution/policy configurations | 448 pass; 8 intentional batch skips out of 456 scheduled tests. |
| Changed lock state, two lock types, three backends, two modes, two policies | 168 executions: native 56/56 match; Observe 48/56 match; regular Incr 32/56 match. |
| Minimal Observe lock reproducer, three fresh caches | The stale `busy` answer reproduces 3/3 times. |

The Bash comparison has 12,234 matching transcript lines per phase after its
reviewed normalization; 70/83 groups match literally without normalization.
The original workflow audit took 212.984 seconds including its wrapper and first
replay checks; the final-policy probe took 152.602 seconds. Most of the live
workflow wait time is deliberate blocked regular-Incr execution.

### The counterexample

Run this small [reproducer](repro_warm_lock.sh) from the repository root:

```bash
./studies/live-workflows-2026-10-09/repro_warm_lock.sh
```

Its actual output, reproduced three times, is:

```text
Held, cold Observe: busy
Released, native: acquired
Released, warm Observe: busy
```

The script exits **1** because the last answer is wrong. It creates its own cache
and removes its scratch directory afterward. The first command runs while an
outside `flock` process holds the lock; `--close` prevents inheriting that lock's
descriptor. After the holder exits, native execution can acquire the lock, but
batch Observe returns the previous contention answer from the retained cache.
The command and lock pathname are unchanged.

The broader corrected probe reproduces this stale answer for **both `flock` and
SQLite**, in **streaming and batch** execution, with **live and final** policies:
eight Observe mismatches. In each, the cold-held command correctly reports `busy`,
then the free warm command incorrectly reports `busy` with retained cache metadata.
All 56 native observations match the lock oracle. The file bytes remain unchanged;
lock ownership is a kernel coordination fact that can change independently of
file content. Replay itself may alter file timestamps, so the evidence records
both before and after state rather than claiming all metadata is immutable.

Regular Incr has 24 mismatches: three held phases for each lock type/mode/policy
combination return `acquired`. Its private file does not share the outside lock,
including when its cache is cleared. This is the original isolation limitation.
Observe's stale warm answer is a **separate cache-correctness limitation**, not
another example of that isolation argument. The sixteen cold examples should not
be presented as proof that all their possible coordination states are safe to
memoize.

The repeated original workflows had **no unchanged Observe cache metadata** across
their warm phases in either policy probe. They establish correct repeated
execution with retained caches, not replay of every live protocol. The 18 actual
hits are established separately by the corrected finite batch probes. A runtime
fix for lock-sensitive reuse would need to preserve live lock operations or
exclude those commands from replay, including handling previously saved entries;
this audit does not modify runtime behavior.

The machine-readable [validation summary](warm-validation.json) and
[compressed evidence](evidence/warm-audit.json.gz) retain the results and hashes.
The negative findings are included and are not counted as successful equivalence.

## Reproduction

After building both repositories and installing the [prerequisites](README.md),
run these commands serially from the Incr repository root. Choose new output
directories; existing evidence is never silently overwritten.

```bash
# Full official Bash corpus, cold/warm, plus live/final streaming regressions.
./studies/bash-parity-audit-2026-10-08/run.sh \
  --output studies/bash-parity-audit-2026-10-08/results/latest

# Live workflows, Bash wrapper, and explicit batch replay/invalidation checks.
python3 -B studies/live-workflows-2026-10-09/warm_audit.py \
  --output studies/live-workflows-2026-10-09/results/warm

# Exploratory: run live protocols under the weaker final-output contract.
python3 -B studies/live-workflows-2026-10-09/warm_audit.py \
  --suite live --live-policy final \
  --output studies/live-workflows-2026-10-09/results/final-probe

# Broaden the focused regression suite beyond streaming defaults.
for policy in live final; do
  python3 -B qualification/regressions.py --effect-policy "$policy" --batch -v
  python3 -B qualification/regressions.py --effect-policy "$policy" --batch --compress -v
  python3 -B qualification/regressions.py --effect-policy "$policy" --full -v
done
```

`warm_audit.py` also accepts `--suite live`, `--suite wrapper`, or `--suite replay`
for focused runs. Each invocation has a four-second process-tree deadline by
default, configurable with `--timeout`. Exact output, status, filesystem checks,
and cleanup are recorded. Sequential positive controls must pass before any
isolation difference can count as evidence. A failure produces a nonzero exit and
retains raw records; an interrupted supervisor preserves its workspace.

## What each layer measures

### Live workflows: same path, retained cache, restored fixtures

Each of the sixteen original scenarios runs under native Bash, regular Incr, and
Observe. The phases are cold, warm-1, warm-2, delayed-warm, and warm-after-delay.
Within each scenario/backend sequence, the work directory is reset at the same
absolute path while the cache is retained. This lets scripts recreate their
initial fixtures without deleting the cache that the earlier command populated.
The nine previously audited consumer-delay variants run in the delayed phase;
the other seven cases simply receive another ordinary repetition.

The original command boundaries and `live` policy remain intact. Delays are
outside the memoized worker and do not alter its command string. Filesystem
checks cover release targets, audit records, cancellation state, duplicate queue
claims, directory-lock cleanup, delivery tickets, and database rows. Observe is
compared to native state; regular Incr is checked against its specific predicted
isolation outcome, including state where applicable.

Restoring fixtures can change inode identities or metadata and correctly force
re-execution. Some blocked regular-Incr executions never finish recording an
entry. Therefore “warm” here means **cache retained from earlier attempts**, not
that every scenario has a reusable entry or that every run hits. Each record
includes before/after cache metadata and how many entries remained unchanged.

The separate `final` probe uses the same scripts with a generated backend helper
that changes only the effect policy. It asks whether each live protocol still
matches its original outcome; a difference is reported explicitly, but is not
by itself a violation of the final-output contract. It must not be used to
relabel a final-policy failure as a defect in live-policy execution.

### Twelve ordinary programs through the Bash wrapper

These tests invoke `incr.sh -b script.sh`, exercising Bash parsing and command
selection rather than only a manually inserted `memo` call. Here `-b` selects
the **Bash parser**; it is distinct from the Rust executable's batch flag.
Both backends are compared with native Bash under both live and final policies.
The programs cover pipelines, `for`, `while read`, command substitution, functions,
conditionals, stderr and exit status, copied output, missing files, symlinks,
globbing, and environment variables.

Each sequence runs cold, twice unchanged, after an input change, unchanged again,
and after restoring the original inputs. Unchanged inputs retain their identities
and timestamps. Changed file content has the same size and its old modification
time is restored. Other changes introduce/remove a file, retarget a symlink,
change directory membership, and alter an environment variable. Copy outputs are
removed before each invocation to exercise output recreation. Stdout, stderr,
exit status, and the output file are compared with the corresponding native run.

Wrapper fallback is a valid way to preserve shell semantics. Cache inventories
make that limitation visible; success does not assert that every shell construct
was accelerated.

### Explicit batch hits and dependency invalidation

For each backend and policy, `cat input` and `cp input output` run in batch mode
with full tracing forced (`-b -f`)
through the same six phases. A launcher writes a small counter **before the tracer
or sandbox starts**, outside the observed command. For the sandbox it counts only
worker launches (`-D`), not output commits. A completed invocation with existing
cache metadata and no new worker launch demonstrates actual batch replay.

Unchanged `cat` phases must demonstrate a hit, as well as returning the right
bytes. Copy phases check restored output and record whether replay occurred;
correct re-execution is not mislabeled as a failed hit. Changed equal-length
content with its old modification time must produce new bytes. These finite
batch tests establish replay separately from the open-ended live workflows,
where batch execution's need for EOF would itself change the protocol.

### Full upstream Bash suite and focused regressions

The existing Bash study verifies its unmodified GNU Bash 5.2.37 corpus, freezes
the current runtime, and compares 83 groups in cold and warm phases. Its full
corpus comparison is **Observe versus native Bash under final policy**; regular
Incr is covered by the new wrapper and command-level comparisons, not by that
83-group matrix. Known diagnostic normalization is documented in the
[Bash study](../bash-parity-audit-2026-10-08/README.md), and raw transcripts remain
available for checking it.

The focused Observe regressions cover actual reuse, output replay, invalidation,
corrupt cache entries, append/read-modify-write, links and permissions, byte paths,
concurrent access to a shared cache, partial/closed streams, inherited descriptors,
and wrapper behavior. The full Bash runner executes streaming live/final
configurations; the commands above add batch, compressed batch, and full tracing
under both policies. Batch runs intentionally skip tests requiring an unbounded
or held-open input stream.

### Changing lock state without changing the command

A separate probe tests `flock` and SQLite transaction reservation with the same
command, pathname, and retained cache while outside ownership changes. It runs
both backends and native execution, with streaming and batch execution, under
both policies:

```bash
python3 -B studies/live-workflows-2026-10-09/coordination_audit.py \
  --output studies/live-workflows-2026-10-09/results/coordination
```

The phases are free/cold, free/warm, held/warm, held/warm again, released/warm,
held with a cleared cache, and free again with that last cache retained. Before
each held phase the controller opens the current filesystem object and acquires
its lock, and keeps it held until the child finishes. Descriptors are not inherited
by the child. This avoids both an inherited-descriptor fallback and accidentally
holding a previous inode after a commit replaces the pathname.

The SQLite worker only begins and rolls back a transaction; it does not insert
rows. Thus contention can change independently of database contents. The probe
records file hashes, inode identities, timestamps, cache metadata, and the actual
answer. Native execution must report `busy` while held and `acquired` while free.
The cleared-cache held phase separates a cold execution problem from a stale
warm answer. Unlike the original isolation matrix, this diagnostic compares
**every backend** to the native oracle and exits nonzero on any difference.


## Audit corrections and evidence provenance

The first batch hit counter counted sandbox launches for regular Incr, but its
read-only tracing path could bypass that launcher. All returned bytes were
correct, yet absence of a sandbox launch alone was insufficient evidence of a
hit. The corrected probe forces full tracing, was rerun for all 48 cases, and
confirms 18 hits: three unchanged phases for `cat` under each backend/policy,
and three for `cp` under Observe with each policy. Regular Incr's copy results
are correct but did not demonstrate hits in this probe. The earlier hit labels
are superseded; the original workflow and wrapper output checks remain valid.

The initial SQLite coordination probe hashed the database after acquiring the
parent's lock. Closing a descriptor for that inode can release this process's
POSIX record locks, so its native reference exposed an invalid test setup. The
corrected probe hashes before locking and now stops on any native-oracle failure.
All 168 observations were rerun after this correction. Only that corrected matrix
is used for the lock findings above.

The evidence archive separates accepted data from `superseded` diagnostics.
It retains both initial harness sources because their fingerprints differ from
the corrected scripts, plus the final sources and each run's recorded hashes.
This preserves provenance without pretending the corrected instrumentation was
used for an earlier run. No runtime source or original scenario was changed.

Before testing, the original live study's generated result directories and scratch
files were removed. Every new owned cache and fixture was removed after its
supervised process tree finished. Fresh raw results were compressed into the
retained evidence archive before their generated directories were removed. The
committed historical evidence, required binaries, dependency installations, and
unrelated repository data are preserved.
