# Live filesystem workflows: Observe versus isolated execution

Sixteen small programs demonstrate why **private filesystem execution followed by
an end-of-command commit cannot preserve live cooperation with outside processes**.
They use cold caches. No stale cache, corrupted entry, parser bug, or performance
claim is involved.

**Warm-cache finding:** the follow-up [audit](WARM_CACHE.md) passes the repeated
workflows but finds stale lock-contention answers under Observe replay. Cold
correctness is not a general warm-cache guarantee.

From the Incr repository root:

```bash
./studies/live-workflows-2026-10-09/run.sh
```

The runner compares each program under native Bash, current Incr with Observe,
current Incr with try/strace, and **try alone without Incr**. The last column is the
design control: the same failure must appear without any cache machinery.

```bash
# Read one program alongside its actual outputs and explanation.
./studies/live-workflows-2026-10-09/run.sh --case 02 --explain

# List scenarios, or select several.
./studies/live-workflows-2026-10-09/run.sh --list
./studies/live-workflows-2026-10-09/run.sh --case 1 --case 11 --case 15

# Run just Observe, or repeat the comparison with fresh fixtures and caches.
./studies/live-workflows-2026-10-09/run.sh --mode observe
./studies/live-workflows-2026-10-09/run.sh --repeat 3
```

`OK` means exact expected native behavior. `DIFF` means the **specific predicted
wrong output**, with a successful exit. `BLOCKED` means a predicted deadlock reached
the deadline after producing its expected diagnostic. `UNEXPECTED` fails the
study; an arbitrary error or timeout never counts as a successful demonstration.
The runner exits zero only when every selected outcome is as predicted.

The checked [validation record](validation.json) identifies the final audit and
its [retained raw evidence](evidence/audit.json.gz): **128/128 matrix outcomes**
(two repetitions of all sixteen cases under all four backends), plus **36 delayed
consumer checks** and five CLI checks. The matrix took 116.7 seconds, with no
surviving descendants. Each selected run must match its exact expected output,
status and cleanup conditions. See [AUDIT.md](AUDIT.md) for the design review,
filesystem checks and corrections made during review.

There are five blocked examples per isolated backend. The default four-second
deadline therefore accounts for at least 40 seconds of a full run; the successful
programs themselves are tiny. Increase `--timeout` on a slow machine. Native and
Observe alone should finish in seconds. Raw stdout, stderr, exit status, timing,
process-cleanup diagnostics, and source/binary hashes go into a new `results/`
directory on every run. `--keep-work` retains fixtures and caches for inspection.

## What to read

The [detailed scenario report](REPORT.md) walks through all sixteen programs,
including execution order, exact outputs, why isolation changes the result, and
what each example does and does not establish.

The [retained-cache audit](WARM_CACHE.md) extends this with repeated live workflows,
Bash-wrapper comparisons, changed-input checks, and explicit cache-hit evidence.
Run it separately from the repository root:

```bash
python3 -B studies/live-workflows-2026-10-09/warm_audit.py \
  --output studies/live-workflows-2026-10-09/results/warm
```

The separate `coordination_audit.py` probe and small `repro_warm_lock.sh` reproduce
the known warm-lock failure; see the audit for commands and interpretation.

Every program is in `cases/`. The only common shell helper is `memo`, which selects
the execution boundary. Its body is one line. There is no TCP checkpoint server,
port discovery, custom event protocol, or timing-based sleep used to order peers.
The short sleeps only back off genuine application polling loops.

There are no coprocesses. Ordinary pipes carry notifications and results; small
receipt/release files provide feedback when a worker must remain alive. Receipt
files read by isolated workers are created before those workers start, then updated
by the caller. They are never written inside the sandbox, so the feedback channel
remains shared while the application's output/control file is private. This avoids
confusing missing feedback with the specific isolation failure being demonstrated.
The queue and lock examples wait for a release file to stand in for work performed
while the claim or lock is held. Every handshake is visible in the example itself.

| Program | Ordinary workflow / shell feature | What isolation changes |
|---|---|---|
| [01](cases/01-spool-pipeline.sh) | Disk queue; pipeline and `while read` | Filename arrives before the file is shared; producer waits for deletion. |
| [02](cases/02-batch-export.sh) | Batch export; `for` loop and receipt file | Consumer repeatedly reads the old batch despite new batch notifications. |
| [03](cases/03-temporary-preview.sh) | Temporary rendered page; `mktemp` and `EXIT` trap | The preview is private throughout its entire lifetime. |
| [04](cases/04-log-monitor.sh) | Background build; log polling and stop file | Monitor never sees the error that should trigger cancellation. |
| [05](cases/05-release-healthcheck.sh) | Symlink deployment; atomic rename and conditional rollback | Outside health check tests the old release. |
| [06](cases/06-shared-audit-log.sh) | Persistent logger; input loop and concurrent append | Whole-file commit loses the peer's already-completed append. |
| [07](cases/07-cancel-worker.sh) | Task worker; cancellation before its next task | Private copy hides the controller's cancellation. |
| [08](cases/08-queue-rename.sh) | Queue worker; atomic move to claim work | A second worker claims the same job in the shared namespace. |
| [09](cases/09-directory-lock.sh) | Cron/deployment exclusion; `mkdir` and cleanup trap | Two jobs each acquire what appears to be the same lock. |
| [10](cases/10-exclusive-claim.sh) | One-time job claim; `set -o noclobber` | Both exclusive file creations succeed in separate views. |
| [11](cases/11-flock.sh) | Deployment lock; `flock` and descriptor redirection | Copy-up separates the new lock inode from the held lock. |
| [12](cases/12-fifo-stream.sh) | Producer advertises named stream; FIFO and pipeline | Outside reader cannot open the private endpoint. |
| [13](cases/13-local-socket.sh) | One-request local helper; Unix socket and background process | Client cannot reach the helper's private socket pathname. |
| [14](cases/14-delivery-receipt.sh) | Delivery acknowledgment; deletion of retry ticket | Shared deletion does not remove the private ticket, so sender retries. |
| [15](cases/15-sqlite-lock.sh) | Two database writers; SQLite transaction | The private database copy does not share the held writer lock. |
| [16](cases/16-tee-stream.sh) | Journaled stream; `tee` in a three-stage pipeline | Stream bytes arrive while the journal is private; acknowledgment cannot complete. |

The SQLite example uses Python's standard `sqlite3` module because the SQLite CLI
is not required. All other examples use Bash and small ordinary command-line tools.

## Why this is a design comparison

These are sixteen applications of a few mechanisms, **not sixteen independent
impossibility results**:

1. **Publication before completion.** A producer publishes a pathname or changes a
   shared file, then continues working or waits for its consumer. Forwarding stdout
   while withholding filesystem changes violates this protocol. Delaying stdout
   until commit instead deadlocks workflows that require a reply before exit.
2. **Shared mutable state.** A copied-up file is no longer the peer's live file.
   Later updates and deletions are invisible to the worker; replacing the file at
   commit can overwrite peer changes. Replaying a final file image cannot in general
   merge arbitrary concurrent operations or undo an already-observed wrong decision.
3. **Shared namespace and object identity.** Claims need a single namespace, and
   file locks need the same underlying object. Private mkdir/create/rename and
   copied-up lock/database files do not provide that shared coordination. FIFO and
   Unix-socket peers also need access to the same published endpoint.

A backend could deliberately share these paths, bypass isolation, introduce a
shared lock service, or provide operation-level synchronization. Those change the
execution contract; fixing a parser or cache invalidation bug does not suffice.
For example, append-aware merging could repair example 06 specifically, but it
would not solve the other protocols.

The comparison uses **the current Incr binary for both Incr backends**, not the
older qualification worktree. Every `memo` call gets fresh cache state. Native and
Observe must agree with a handwritten expected output, and both isolated modes
must agree with their specific predicted failure. A sequential file-write/read
positive control must first pass under every selected backend. Setup failure,
unexpected stderr, unexpected exits, or surviving descendants fail the run.

## Boundary and scope

`memo bash -c '...'` represents an external shell worker; `memo python3 ...` is an
external database worker. The enclosing controller/consumer remains outside that
boundary. This is intentional: the workload is cooperation **across** a command
boundary. Isolating the entire cooperating application as one unit can hide some
of these differences. Serial commands which finish and commit before their outputs
are consumed can work correctly; the positive controls demonstrate that case.

The study invokes the command-level interface directly. It does not claim the AST
wrapper automatically wraps every construct shown here. Native fallbacks in the
script transformer can avoid a problem by declining to accelerate it.

Observe explicitly uses `--effect-policy live`, because intermediate observations
and interactions are part of these programs' contract. The current default `final`
policy does not promise those semantics. These **cold-run** examples demonstrate
live tracing versus isolation; they do not establish safe warm-cache reuse for
arbitrary concurrent programs, cache-hit rates, or speedups. Locks and socket/network
state are especially not general memoization inputs.

## Prerequisites

Linux x86-64 with working ptrace and user/mount namespaces, Bash, Python 3, GNU
coreutils, util-linux (`flock`, `unshare`), OpenBSD netcat (`nc -N -U`), strace,
mergerfs/FUSE, `getfattr` (the `attr` package), and noninteractive `sudo -n` for
Incr's sandbox cleanup. The sandbox positive control checks that the actual host
can run the backend. Nothing is downloaded by the runner.

Build once from the Incr repository root:

```bash
cargo build --release
(cd ../observe && cargo build --release)
```

The runner uses the existing `qualification/bounded.py` process-tree supervisor.
It reaps descendants after intentional deadlocks and removes only its uniquely
owned `.work/run-*` directory, after checking cleanup and visible mounts. Results
remain separate. No runtime source changes are needed for this study.
