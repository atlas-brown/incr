# Audit of the live-filesystem examples

The final examples use ordinary pipelines and background jobs, with **zero
`coproc` invocations**. The comparison targets cooperation across a command's
private filesystem boundary, using current Incr for both execution backends.

## Ordering and attribution

| Cases | Ordering checked | Why the isolated result is a design difference |
|---|---|---|
| 01, 12 | The producer writes the file / creates the FIFO before printing its pathname. It cannot finish until the outside consumer participates. | The pathname is published over stdout while its target remains private. Waiting for completion before forwarding stdout would also block the protocol. |
| 02 | Each batch is written before its notification; the next overwrite waits for the matching receipt. | The consumer sees the original batch file, not a race between overwrites. |
| 03 | The renderer waits for the preview acknowledgment before its cleanup trap runs. The pipeline is joined before checking cleanup. | The missing preview is private, not removed too early by an unsynchronized trap. |
| 04, 16 | The controller waits for the actual log/journal contents. The producer stays alive until acknowledgment. | The private write cannot trigger the outside acknowledgment. `tee` is allowed to write stdout before its file; the consumer polls the file rather than assuming a write order. |
| 05 | The atomic release switch completes before the health-check request. The deployment waits for its verdict. | The outside check sees the old release despite the completed private switch. |
| 06 | The logger appends before emitting confirmation. The caller appends before allowing the logger's input to reach EOF. | Both appends completed, in a defined order; committing the private file loses the outside append. |
| 07, 14 | The worker writes its control/ticket file before notifying the caller. The caller changes/deletes it before acknowledging. | The copied-up file masks a later peer mutation, so the worker processes cancelled work or retries acknowledged delivery. |
| 08–10 | The first move/mkdir/exclusive create succeeds before the outside contender runs. The first worker remains alive until release. | Claims are made in different namespaces; this is not an uncontrolled race between contenders. |
| 11 | The outer `flock` holds the lock throughout the inner attempt. `--close` removes its descriptor from the child's inherited descriptors. | Opening the lock file for write copies it up, so the second lock refers to another object. Observe really executes through Incr rather than taking its extra-descriptor fallback. |
| 13 | The server creates the socket before notification; the client retries the short bind-before-listen window. | The isolated socket's pathname is unavailable outside, even though the server announced readiness. |
| 15 | The parent acquires SQLite's immediate transaction before starting the competing writer; it rolls back afterward. | The private database inode does not share the already-held writer lock. Unexpected SQL errors are raised, not classified as expected contention. |

Feedback files read by isolated workers exist before the worker starts and are
modified only by the caller. The worker never copies them up by writing them.
This keeps the acknowledgment channel usable while isolating the application
state being demonstrated. The scripts deliberately avoid depending on discovery
of newly created feedback paths through an overlay's cached directory view.

## Corrections made during review

The earlier coprocess versions of cancellation and delivery had a real test-side
race: Bash can close a coprocess descriptor when it reaps the child, before the
caller reads the final reply. Two hundred ordinary repetitions missed it, but
delaying the caller reproduced `Bad file descriptor` in both cases. The final
pipeline versions eliminate that descriptor-lifetime dependency altogether.

The runner now fingerprints sources, helpers and binaries **before** execution
and checks them again afterward. A changed input invalidates the run. Exceptions
retain the workspace if the supervisor did not return a cleanup result. Cleanup
checks both a mount at the workspace itself and descendant mounts, including
mountinfo paths with escaped characters.

## Verification and retained evidence

[validation.json](validation.json) records the final checks, fingerprints and the
compressed raw-evidence archive. The archive preserves each invocation's stdout,
stderr, exit status, timeout flag, process-tree diagnostics and cleanup result.
It is committed with the study; it does not depend on ignored local `results/`
directories being available in another checkout.

The full matrix uses fresh fixtures and empty caches for every case/backend/run.
Sequential positive controls must first pass under all four backends. Exact
expected outputs and statuses are required: arbitrary crashes, stderr, missing
records, unexpected timeouts and surviving descendants cannot count as evidence.
The separate audit checks delay consumers, exercise CLI rejection, and examine
the retained private-file payloads behind blocked examples.

This establishes the tested **cold, live-policy** behavior. It does not claim
arbitrary concurrent warm-cache correctness, automatic AST wrapping of these
whole examples, performance improvement, or sixteen independent impossibility
results. The sandbox-only column and the ordering above establish why the
observed failures come from private execution plus final commit, rather than
Incr cache or parser defects.
