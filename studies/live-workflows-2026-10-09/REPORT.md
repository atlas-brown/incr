# Detailed report: sixteen live filesystem workflows

These programs show a specific limitation of running one cooperating command in a
private filesystem and publishing its changes only after it exits. A command's
stdout can reach another process while its files remain private. Its private
copies can also stop sharing updates, namespace ownership, and locks with peers.
The examples make those differences observable with ordinary shell workflows.

This report explains the scripts committed in `e4a9c40`. It uses the retained
[validation record](validation.json) and [raw evidence](evidence/audit.json.gz).
The scripts and their verified fingerprints are unchanged by this report.
See the [README](README.md) for prerequisites and the [audit](AUDIT.md) for review
checks. All sixteen programs use ordinary pipes or background execution; none
uses `coproc`.

The subsequent [warm-cache audit](WARM_CACHE.md) checks repeated execution and
actual replay separately. It confirms these repeated workflows but also finds
stale lock-contention answers under Observe when outside lock state changes.
That finding is separate from this report's cold isolation argument.

## How to interpret the comparison

The small `memo` helper selects the execution backend for one external command.
The enclosing consumer or controller stays outside that command's boundary.
Case 11 invokes the backend directly under `flock`; case 15 invokes it from Python.

| Backend | Execution contract in this study |
|---|---|
| Native | Execute the command directly against the shared filesystem. |
| Observe | Execute through current Incr with Observe and explicit `--effect-policy live`. Filesystem effects remain visible during execution. |
| Regular Incr | Execute through the same Incr binary using its try/strace isolation backend, then commit filesystem effects. |
| Standalone sandbox | Execute with try and then commit, without Incr, caching, or its tracing machinery. |

Every case starts with fresh fixtures and an empty cache. In the sections below,
“isolated” means **both regular Incr and standalone try**, which produced the same
listed result. Native and Observe likewise agreed in every recorded run.
A completed example exits zero; a blocked example reaches the supervisor's
four-second deadline and is terminated and reaped. Its displayed output is the
output captured before termination. A timeout alone is not the argument: the
execution order identifies the dependency that cannot be satisfied.

Some examples use a tiny receipt or release file to order the participants.
Feedback files read by isolated workers are created outside before the worker
starts, and only the outside process writes them. They therefore remain in the
shared lower filesystem instead of becoming private copies. This makes the
feedback channel usable while the application file under examination is private.
The `.02`-second sleeps only reduce polling load; no example assumes that another
process finishes within a chosen sleep interval.

## 01. Disk-backed queue with deletion acknowledgment

[Source: 01-spool-pipeline.sh](cases/01-spool-pipeline.sh)

**Workflow and order.** A producer writes an invoice into `spool/job`, prints the
pathname through a pipe, then waits for the file to disappear. The downstream
`while read` loop reads the invoice and removes the file. Deletion acknowledges
consumption and supplies backpressure: the producer cannot exit before the
consumer handles the job.

**Native and Observe:**

```text
invoice 42
```

**Isolated, blocked:**

```text
spool: unavailable
```

The notification follows the file write, so the consumer is not simply faster
than the producer. Isolation lets the pathname cross the pipe while keeping the
file private. The consumer cannot read or remove it. The producer keeps waiting
for removal, so it cannot reach the commit that would publish the file. The audit
found the invoice in the private filesystem and no corresponding shared file.

This models a queue that passes paths instead of copying large payloads through
stdout. A finite command whose caller reads its files only after exit would not
have this dependency. Buffering the pathname until exit would also prevent this
particular producer from receiving its required acknowledgment.

## 02. Reusing a batch export file

[Source: 02-batch-export.sh](cases/02-batch-export.sh)

**Workflow and order.** `batch.csv` initially contains `empty`. A `for` loop writes
three batches—north, south, west—to that same file. After each write it prints the
filename and waits for a matching receipt. The consumer reads the file before
writing that batch's receipt. Thus the exporter cannot overwrite a batch before
its consumer has read it.

**Native and Observe:**

```text
north,10
south,10
west,10
```

**Isolated, completed:**

```text
empty
empty
empty
```

The consumer sees the original shared file at every notification. The independent
receipt channel still works, allowing the loop to finish normally despite all
three incorrect reads. Publishing the last private version at exit cannot repair
the batches already consumed. Delaying the consumer was also tested; the receipt
prevents an overwrite race in the native execution.

This is a repeated export or report stream with one reusable output path. Its
point is the relationship between each notification and the corresponding file
version, not merely whether the final file eventually contains new data.

## 03. Temporary preview with cleanup

[Source: 03-temporary-preview.sh](cases/03-temporary-preview.sh)

**Workflow and order.** A renderer creates a temporary directory using `mktemp`,
writes `index.html`, and publishes its pathname. An `EXIT` trap owns cleanup.
Before exiting, the renderer waits for the caller's `viewed` acknowledgment.
The caller reads the preview if available and acknowledges the attempt. After
the pipeline joins, the script checks that the temporary directory is gone.

**Native and Observe:**

```text
<h1>Preview</h1>
preview: cleaned
```

**Isolated, completed:**

```text
preview: unavailable
preview: cleaned
```

The preview exists throughout the caller's attempted read, but only in the private
filesystem. The acknowledgment then permits the cleanup trap to remove it before
commit. Its entire useful lifetime disappears from the final filesystem image.
The delayed-consumer audit checks that this is not premature cleanup racing the
caller. Both executions successfully clean up; only one serves the preview.

This captures temporary renderers, generated previews, and similar helpers whose
outputs are intentionally available during the helper's lifetime rather than
retained after it exits.

## 04. Monitoring a running worker's log

[Source: 04-log-monitor.sh](cases/04-log-monitor.sh)

**Workflow and order.** A background worker announces startup, appends an error to
`build.log`, and waits for a stop file. The foreground controller polls the log.
On seeing the error it announces cancellation, creates the stop file, and waits
for the worker to finish.

**Native and Observe:**

```text
worker: started
monitor: stopping build
```

**Isolated, blocked:**

```text
worker: started
```

The controller never sees the private log append, so it never issues cancellation.
The worker waits for that cancellation and cannot exit to publish the log. The
audit found `ERROR: missing source` in the private log and an empty shared log.
The dependency is log visibility before shutdown, not a short monitoring deadline.

The stop file is created only after the controller sees the error. In the isolated
run execution never reaches that step, so the explanation does not depend on
whether a newly created stop file would be discoverable inside the sandbox.
The tiny worker represents the control protocol of a longer build or service.

## 05. Deployment switch followed by a health check

[Source: 05-release-healthcheck.sh](cases/05-release-healthcheck.sh)

**Workflow and order.** Two release directories contain version markers. `current`
initially points at v1. The deployment worker creates a v2 symlink and atomically
renames it over `current`, then asks the caller to check the deployed path. It
waits for a verdict and rolls back to v1 if the verdict is unhealthy.

**Native and Observe:**

```text
healthcheck: v2
```

**Isolated, completed:**

```text
healthcheck: v1
```

The outside check follows `current/index` after the worker has completed its
private switch. It still reaches v1 and reports failure. The worker consequently
rolls back a release that the caller never had the opportunity to inspect.
Filesystem checks confirm the final target is v2 under native/Observe and v1
under isolation. Delayed checks preserve this outcome.

The example models a health check by reading a release marker; it does not run an
HTTP server. Its relevant requirement is that a consumer of the deployment path
must observe the switch before deciding whether to accept it. Atomic rename
within a private namespace does not provide that outside visibility.

## 06. Two participants append to an audit log

[Source: 06-shared-audit-log.sh](cases/06-shared-audit-log.sh)

**Workflow and order.** A three-stage pipeline feeds `worker` to a persistent
logger. The logger appends that record to `audit.log` before confirming it on
stdout. The downstream participant then appends `peer` and signals the upstream
stage to finish. Only then can the logger receive EOF and exit.

**Native and Observe:**

```text
worker
peer
```

**Isolated, completed:**

```text
worker
```

This ordering ensures both appends completed before the isolated logger exits:
worker append, confirmation, peer append, upstream completion, logger EOF.
The logger's private file contains its own append, while the outside process
updates the shared file. Committing the private file image loses the peer's
already-completed append. The final file contents were checked in the audit.

This case demonstrates a limitation of final-image commit for concurrent writes.
An append-aware merge could repair this particular protocol; the example does
not prove every possible commit algorithm must lose every concurrent append.
Such merging would not, by itself, repair live publication or shared locks.

## 07. Cancellation before the next task

[Source: 07-cancel-worker.sh](cases/07-cancel-worker.sh)

**Workflow and order.** The worker writes `running` to `job.state`, announces
readiness, and waits for `next-task`. The controller first writes `cancelled` to
`job.state`, then releases the next task. The worker reads its state only after
that release and decides whether to process the task.

**Native and Observe:**

```text
cancelled
```

**Isolated, completed:**

```text
processed: expensive-task
```

The controller's cancellation precedes the worker's decision. However, the
worker's earlier write created a private state file, hiding the controller's
later update. The separate task-release file remains shared, so the worker wakes
up and makes the wrong decision using `running`. Final-state checks also show
that commit restores `running` instead of preserving `cancelled`.

The script prints the processing decision rather than performing expensive work.
It tests the correctness of the cancellation protocol, including its ordering,
without requiring a slow workload. Delayed consumption of the reply also passed.

## 08. Claiming a queued item by rename

[Source: 08-queue-rename.sh](cases/08-queue-rename.sh)

**Workflow and order.** The first worker claims `inbox/job` by moving it to
`working/first`. After that move succeeds it announces the claim and remains
active. The outside worker then tries moving the same inbox path to
`working/second` before releasing the first worker.

**Native and Observe:**

```text
queue: already claimed
```

**Isolated, completed:**

```text
queue: duplicate claim
```

In the shared filesystem, the first move removes the source path for everyone.
The second move therefore fails. Under isolation, removal of the source and
creation of the destination occur in the first worker's private view. The shared
inbox still contains a claimable item, so the second move succeeds too. The audit
confirmed both destination files exist after the isolated execution.

The directories are on the same filesystem in these fixtures. The example uses
the common atomic-rename queue pattern and explicitly orders the competing
claims; it does not depend on simultaneous, ambiguously ordered moves. Publishing
the first claim later cannot undo work already authorized by the second claim.

## 09. A directory used as a lock

[Source: 09-directory-lock.sh](cases/09-directory-lock.sh)

**Workflow and order.** A deployment worker acquires `deploy.lock` with `mkdir`,
installs an `EXIT` cleanup trap, and announces acquisition. It holds the directory
until released. The caller tries the same `mkdir` while that first critical
section is still active, then sends the release.

**Native and Observe:**

```text
deploy: busy
```

**Isolated, completed:**

```text
deploy: overlap
```

A shared namespace gives `mkdir` one winner: an existing directory prevents the
second acquisition. A private directory does not exclude an outside creator.
Both participants can therefore believe they hold the lock during overlapping
critical sections. Both eventually clean up; the audit verifies no lock directory
remains, showing why final-state inspection alone would miss the violation.

The release handshake stands in for the useful work done while holding the lock.
It keeps the first lock held until the second attempt without relying on a timed
sleep. This is the directory-lock idiom commonly used by shell cron jobs.

## 10. Exclusive creation of a job claim

[Source: 10-exclusive-claim.sh](cases/10-exclusive-claim.sh)

**Workflow and order.** With `set -o noclobber`, the first worker creates
`job.claim` containing `first`. It announces success and waits. The outside
participant then tries an exclusive creation at the same path containing
`second`, before allowing the first worker to finish.

**Native and Observe:**

```text
claim: already owned
```

**Isolated, completed:**

```text
claim: duplicate owner
```

Both exclusive creations succeed under isolation because each participant checks
and creates in a different view. The problem is not Bash neglecting its exclusive
creation rule: each operation can satisfy that rule locally while the overall
ownership protocol fails. A later commit cannot retract the second successful
ownership decision.

This is the same shared-namespace family as the directory lock, expressed as a
content-bearing claim file that can outlive a worker. It adds a familiar shell
feature and a different application protocol, not a separate impossibility theorem.

## 11. `flock` on a copied-up lock file

[Source: 11-flock.sh](cases/11-flock.sh)

**Workflow and order.** An outer `flock` process holds an exclusive lock on
`deploy.lock` while running the backend command. The child opens that pathname
for append on descriptor 9 and attempts a nonblocking exclusive lock. The outer
process retains its lock throughout the attempt.

**Native and Observe:**

```text
lock: busy
```

**Isolated, completed:**

```text
lock: overlap
```

In native execution, the child independently opens the same file object and its
lock conflicts with the parent's. Under isolation, opening for write copies the
file up. The child's lock can then succeed on a different underlying object even
though the pathname spelling is identical. Final file contents cannot express
or restore the mutual exclusion that was required during execution.

The outer command uses `--close` to avoid passing its lock descriptor to the
child. The parent still holds the lock, while the child performs a genuinely
separate acquisition. This also avoids Incr's extra-descriptor fallback; Observe
capture was verified. The result concerns this write-open/copy-up pattern, not a
claim that every conceivable use of file locking must fail under isolation.

## 12. Publishing a named pipe

[Source: 12-fifo-stream.sh](cases/12-fifo-stream.sh)

**Workflow and order.** A producer creates `events.fifo`, publishes its pathname,
and opens the FIFO to write one event. The downstream reader checks the advertised
endpoint and uses `cat` to read it. A FIFO writer waits for a reader to open the
same endpoint, providing the rendezvous naturally.

**Native and Observe:**

```text
event: uploaded
```

**Isolated, blocked:**

```text
fifo: unavailable
```

The FIFO is created before publication, but it exists only in the private
namespace. The outside reader cannot open it. The producer blocks opening the
FIFO for writing and cannot exit to publish its filesystem changes. This is
stronger than a missing final output: the private endpoint cannot provide the
live communication required for the command to finish.

The example creates a new FIFO inside the command. It does not establish that
all uses of preexisting, deliberately shared FIFOs fail. It also uses an ordinary
anonymous pipeline for discovery, so endpoint discovery itself remains functional.

## 13. A one-request Unix-socket helper

[Source: 13-local-socket.sh](cases/13-local-socket.sh)

**Workflow and order.** A background `nc` server listens on `helper.sock` and serves
one health reply. Its parent waits until the socket pathname exists, announces
readiness, then waits for the server. The caller checks the advertised pathname
and connects with another `nc` process.

**Native and Observe:**

```text
reply: healthy
```

**Isolated, blocked:**

```text
socket: unavailable
```

The outside client cannot resolve the private socket pathname. The server remains
waiting for its client, and the worker remains waiting for its server, so neither
reaches a useful final commit. Native and Observe expose the same endpoint to
both participants and finish after the single reply.

Socket creation can become visible just before the server calls `listen`. The
client retries connection attempts to cover that legitimate startup window.
The isolated result instead fails the pathname check itself. This is a small
local helper, with no network service or long-running daemon required; the claim
concerns pathname Unix sockets created inside the isolated command.

## 14. A deleted ticket acknowledges delivery

[Source: 14-delivery-receipt.sh](cases/14-delivery-receipt.sh)

**Workflow and order.** A pending ticket exists before the worker starts. The
sender replaces its contents with `invoice-42`, emits that invoice, and waits
for a receipt. The consumer receives it, deletes `pending`, and only then writes
the receipt. The sender checks whether the ticket remains to decide whether
another delivery attempt is needed.

**Native and Observe:**

```text
consumer: invoice-42
sender: delivered
```

**Isolated, completed:**

```text
consumer: invoice-42
sender: retry
```

The sender's write made a private ticket. Deleting the shared ticket does not
remove that private copy, even though deletion precedes the receipt and the
sender's check. The sender chooses an unnecessary retry. Final-state checks show
the private ticket is also published again by commit, resurrecting acknowledged
work. Native and Observe leave it deleted.

Precreating the ticket lets the consumer's `rm` succeed in every backend, keeping
the example focused on missed deletion rather than a missing initial pathname.
The script prints the retry decision; it does not actually send a second invoice.
Together with case 07, this covers both modification and deletion by a peer.

## 15. SQLite's writer exclusion

[Source: 15-sqlite-lock.sh](cases/15-sqlite-lock.sh)

**Workflow and order.** Python's standard `sqlite3` module creates a database and
starts `BEGIN IMMEDIATE`, holding its writer reservation. While that transaction
is still active, it invokes a second Python writer through the selected backend.
The second writer tries an insert and commit with `timeout=0`; the parent rolls
back only after the child returns.

**Native and Observe:**

```text
database: writer blocked
```

**Isolated, completed:**

```text
database: concurrent writer
```

Both shared-file executions respect the existing writer lock. Isolation gives
the second writer a private database object, whose lock does not conflict with
the lock held on the shared database. Its insert succeeds, and the later commit
publishes that private result. The filesystem audit found no inserted rows in
native/Observe and the `second` row after isolated execution.

The lock error is an immediate SQLite result, not a supervisor timeout; unexpected
SQL errors are raised instead of being counted as contention. This uses a real
database transaction to show the application consequence of separated file
identity. It does not demonstrate a SQLite implementation defect or claim that
the example exhausts the possible database corruption and recovery concerns.

## 16. A stream whose journal must be visible before acknowledgment

[Source: 16-tee-stream.sh](cases/16-tee-stream.sh)

**Workflow and order.** A producer sends `record 42` and holds its output open
until acknowledgment. `memo tee journal` forwards the record and writes a journal.
The consumer prints the received record, waits until it can also read it from
`journal`, and only then creates the acknowledgment that releases the producer.

**Native and Observe:**

```text
stream: record 42
journal: verified
```

**Isolated, blocked:**

```text
stream: record 42
```

The anonymous pipe works: the record arrives. The private journal write does not
become visible outside, preventing acknowledgment. That keeps the producer's pipe
open, preventing `tee` from receiving EOF and exiting to commit. The cycle is:

```text
producer waits for acknowledgment
  -> consumer waits for shared journal contents
  -> journal publication waits for tee to exit
  -> tee waits for producer EOF
  -> producer waits for acknowledgment
```

The audit confirmed the private journal contains the record while the shared
journal is empty. Because `tee` may write stdout before its file, the consumer
polls the journal rather than assuming that receiving stdout proves the write
has completed. This tests visible journal contents, not `fsync` or crash durability.
The isolated command here is just `tee`, making it an especially small example
of a filesystem side effect participating in a streaming protocol.

## What the verification establishes

The retained matrix contains two repetitions of sixteen cases across four
backends: **128 verified outcomes**, comprising 64 native/Observe successes,
44 completed isolated differences, and 20 expected isolated blocked runs.
The matrix took 116.669 seconds. Each selected backend also passed a sequential
write/read positive control, showing that ordinary completed-file publication
works in the tested environment.

Verification requires exact stdout, clean stderr, the expected timeout status,
zero exit status for completing runs, and no leaked or surviving descendants.
An unrelated crash or arbitrary timeout cannot count as a demonstration. The
supervisor terminates and reaps deliberately blocked process trees.

Additional retained checks include 36 delayed-consumer runs, five CLI checks,
20 filesystem check groups, syntax checks, and ShellCheck at warning severity.
All 32 Observe matrix invocations produced capture files, confirming execution
through the capture path rather than simply falling back to native execution.
Source, helper, and binary fingerprints were checked before and after the matrix.
The archive includes raw output and process-cleanup diagnostics, not just a table
of claimed passes.

These are measurements of the committed scripts on the recorded environment,
not a claim that every future platform or implementation must produce identical
diagnostics. The standalone-try comparison and explicit ordering attribute the
observed failures to private execution and final commit without depending on
Incr cache hits, cache invalidation, or shell transformation bugs.

## Design implications and limits

The sixteen workflows illustrate three related requirements:

1. **Effects visible before completion:** cases 01–05, 12, 13, and 16 need a peer
   to observe an intermediate file, path, or endpoint while the worker is alive.
2. **Shared mutable state:** cases 06, 07, and 14 require concurrent appends,
   updates, or deletion to remain meaningful across participants.
3. **Shared ownership and object identity:** cases 08–11 and 15 require claims
   or locks to coordinate access to the same namespace or underlying object.

Several examples deliberately overlap mechanisms. They provide diverse shell
idioms and application consequences, not sixteen independent theoretical proofs.
A backend can support particular workflows by sharing selected paths, declining
isolation, providing shared locking, or introducing operation-aware synchronization
and merging. Those approaches change or extend the execution contract; improving
cache keys or correcting a parser cannot supply the missing live relationship.

The boundary matters. Isolating all participants together can conceal some of
these differences, and sequential workflows that consume outputs after completion
can work. The study directly chooses the command boundary; it does not claim the
AST transformer automatically wraps each entire script as shown.

Finally, Observe is run with explicit **live** effect policy and cold caches.
The default `final` policy does not promise preservation of these interactions.
Successful traced execution here does not establish safe warm-cache replay of
arbitrary concurrent programs, complete tracking of lock or socket state, or any
speedup. The demonstrated benefit is preserving the live filesystem cooperation
of these executions.

## Running and inspecting an example

From the Incr repository root, after meeting the README's prerequisites:

```bash
# Show one script and all four observed outcomes.
./studies/live-workflows-2026-10-09/run.sh --case 16 --explain

# Reproduce the two-repeat matrix with fresh fixtures and caches.
./studies/live-workflows-2026-10-09/run.sh --repeat 2

# Inspect successful live executions quickly.
./studies/live-workflows-2026-10-09/run.sh --mode observe
```

A full single sweep includes five intentionally blocked cases under each isolated
backend. With the default four-second deadline, those waits alone take at least
40 seconds. Use the native or Observe mode for a quick walkthrough, and the full
comparison to reproduce the isolation evidence. The runner's `--keep-work` option
retains fixtures for inspection; every run writes separate result records.
