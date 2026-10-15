# Current checkpoint

The persistent goal is active and incomplete. Annotations remain off in both systems. The replay implementation checkpoint records current source/binary evidence in REPLAY_REUSE_CHECKPOINT.json. Observe ec35e0e is committed; Incr is being checkpointed. Full Bash reruns, real-input scaling and final evaluation remain required; a final clean checkpoint must be pushed before the full matrix.

The first full historical pass was intentionally interrupted after 186/276 valid checks, with ten completed families. All raw evidence remains. Spell/weather were near parity (1.14%/3.13% slower in one repetition); the user explicitly deprioritized such small differences. Focus on material bio regressions, not speculative streaming redesigns.

`guarded-inherited-bio-paper-01` completed 21/21 correctness checks, but Observe was slower: Bash 293.975s, original 265.945s, Observe 360.609s. Its `bio-review.json` and `diagnosis/cache-after-bio-4` preserve evidence: no replay barriers, but 66 warm entries were rewritten. Do not present that diagnostic as a performance success.

Two general replay bugs were then identified and fixed:

- Incr filesystem-effect replay copied bytes without preserving mtime, invalidating unchanged downstream readers. Replay now restores file mtime; cache format 33 / effect manifest 4. A producer-consumer regression checks existing-file overwrite reuse and unchanged downstream cache metadata. Permission-denied timestamp restoration conservatively leaves consumers invalidated rather than breaking group-writable replay.
- Observe's internal pre-write checksum called record_read, accidentally treating its own hash as tracee content consumption. It now records a write precondition, preserving overwrite eligibility. Real tracee reads/stat probes still prevent overwrite reuse. A regression in t_overwrites.sh covers hashing an existing output.

Small command-level diagnostic `results/maintenance/replay-mtime-bio-profile-03` now shows zero recomputation on bio version 4, only idxstats/awk on version 5, and only gnuplot on version 6. This is diagnostic evidence, not independently validated timing or full-size proof. The earlier timestamp-only minimum diagnostic passed 14/14 but still had remaining misses.

`replay-reuse-min-bio-02` completed 21/21 valid checks: version 4 rewrites zero entries, version 5 two and version 6 one. Version 4 took 0.247s versus ~1.01s before the two fixes (diagnostic cohorts, not paired final results).

The first real-BAM .01 diagnostic `bio-replay-real-01pct-02` failed at version 5 with an unexpected diagnostic/recovery (`unreadable syscall exit`). Prior versions validated and version 4 reused all entries, but the run is NOT a successful cohort. Complete failed fixture/cache/capture state is preserved under that run's `diagnosis/`; do not delete or pool it.

Further general Observe fixes now handle cancellation by draining stops without querying deliberately killed tracees, reaping through ECHILD, and retrying EINTR in pre-syscall snapshot copies. A new 200-case cancellation stress test alternates single and forked writers and verifies exact restoration. Initial narrow ESRCH handling was insufficient; retained stress logs expose EINTR, then the final stress and full integration passed.

The initial full installed-Bash run completed with 81/82 cold matches and 82/82 warm matches. Its only failure is printf/cold: shell-start clock differs by one second. Zero cache entries, warm exact match; native prior evidence also shows clock-boundary diagnostics. Preserve the failed full run and do not change comparison rules. The worker is terminal. Relaunch complete custom Bash 5.2.37 defaults and complete installed Bash 5.1.16 benchmark-flags rerun with a fresh ID; both are mandatory. Both are mandatory. Inspect service MainPID, `results/maintenance/replay-reuse-bash-status.json`, per-run logs and saved case records. No performance measurements may overlap this service. Its job-control cases have deliberate ~62-second waits per mode/phase and live 30-second progress messages.

Current component checks: Incr Rust 37 ordinary passes plus foreign-ownership test explicitly run and passed, Observe Rust 8, strict Clippy both, general final regressions 73/73 before cancellation changes (rerun by full Bash driver), live regressions 72 pass + one existing policy-specific skip, descriptor regressions 6/6 before cancellation changes, Observe full integration now 435/435 including cancellation stress. Full Bash results remain pending.

New production paired reporter `studies/paper-size-benchmarks/harness/cohort_report.py` has six synthetic-fixture test groups covering exact paired totals, reversed mode order, provenance mismatch, bad/incomplete evidence, and explicit validation under python -O. Use it after final >=3 matched repetitions, not the archived unvalidated draft. Checkpoint evidence bundles under `checkpoint-evidence/replay-reuse/` preserve separate diagnostics and failed cohorts; each member and archive was round-trip hash verified. Refresh component/Bash evidence after final qualification.


Next: finish/review both full Bash suites. Then rerun .01 after the cancellation fix, followed by serial real-BAM scaling at fractions .01 and .1 using `studies/observe-performance-regression/harness/bio_scale.py` (deterministic seed 42, original scripts and independent native validators). These are subsampling diagnostics, never historical full results. Validate the driver; run no builds/tests alongside timings. Reconfirm full bio, all final Bash/component/scaling gates, and commit/push both clean implementations. Then fresh complete historical evaluation with at least three paired repetitions plus separate full supplemental coverage. Do not pool older implementation cohorts. Report all regressions and historical/native sanity honestly.

`checkpoint-evidence/guarded-descriptors/cohort_report.py` remains an unvalidated analysis draft; validate positive/negative fixtures before final use. Keep all earlier cohorts and failures.
