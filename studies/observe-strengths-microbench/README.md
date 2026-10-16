# Observe strengths microbenchmarks

Seventeen actual [shell programs](scenarios/) exercise deliberately synthetic strengths, meaningful incremental workflows, and negative controls. [PLAN.md](PLAN.md) fixes the methodology, workload-specific edits, scales, assumptions and final acceptance criteria. No background evaluation is launched by importing a module or preparing inputs.

From the Incr root, build current Incr, sibling Observe, and the pinned original comparison checkout described in [the benchmark runner](../paper-size-benchmarks/README.md). The installed parser environment must be available at `qualification/.venv`. A C compiler, GNU time, standard GNU text/file tools, OpenSSL, strace, mergerfs/FUSE and noninteractive sudo are required. No downloaded application datasets or ML dependencies are used.

```bash
# Independent small pilot. Profiling changes measurement overhead: do not pool it with final timings.
bash studies/observe-strengths-microbench/run.sh --run-id my-pilot --scales small --repetitions 1 --diagnostic

# Fresh final experiment, all scenarios/scales, three independent paired repetitions.
bash studies/observe-strengths-microbench/run.sh --run-id my-final --repetitions 3
python3 -B studies/observe-strengths-microbench/harness/audit.py --require-full studies/observe-strengths-microbench/measurements/my-final
```

Use `--only` to select comma-separated scenario names, `--scales` for small/medium/large and a new run ID for each independent attempt. `--sandbox` adds current Incr without Observe for backend attribution. It is an optional diagnostic, not silently substituted for the historical baseline. Cases run serially with exclusive workspace locking, deadlines, process-tree ownership, input/output validation and disk limits. There is no resume/overwrite of existing measurements.

Each episode starts with a fresh cache/fixture and preserves them across six phases. Shell transformation and fixture validation are outside timings. Both engines use the same supported Python transformer and deterministic frontend selection; every static external command must be wrapped. Native Bash establishes independent references. Instrumentation descriptors are stripped before execution, while actual shell-created descriptors remain intact. Plain Bash cannot be expected to lose on every cheap or builtin-only case.

All detailed measurement records live under `measurements/`; generated fixtures, caches and frozen executable copies are disposable under ignored `.work/`. Runtime source snapshots and binary fingerprints identify what was measured. Pilots, invalid instrumentation trials and final measurements are labelled separately and must never be pooled. Final timings disable profiling. The final report requires all 2,754 invocations to pass independent coverage and raw-capture audits.

Pilot history: `pilot-01` is invalid for performance because GNU time's descriptor caused native fallback; its later descendant check also mistook a reaped zombie for a live leak. Subsequent incomplete trials exposed unsupported partial instrumentation in the default AST paths and an overly literal static-count check that counted the shebang. These are framework diagnostics, not final performance samples. The framework chooses the first fully instrumenting frontend (Bash, then dash) identically for both engines, verifies real backend profiles in pilots, and uses the existing benchmark supervisor/descriptor launcher. Early cache-entry counters that searched for `data` rather than `data.incr` are not used as reuse evidence; executor profiles remain available. Final cache counters use the actual on-disk filename.
