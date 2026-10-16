# Studies and maintained runners

- [Consolidated measurements](evaluation-checkpoint-2026-10-16/README.md): canonical detailed old/new measurements from both repos, all qualification and diagnostic evidence, and the explicitly cancelled partial full run. No jobs are queued.
- [Benchmark runner](paper-size-benchmarks/README.md): supported three-mode historical and supplemental comparisons, input preparation, strict output validation and resource supervision. This directory contains code/methodology; generated results are ignored until explicitly consolidated.
- [Bash correctness runner](bash-parity-audit-2026-10-08/README.md): supported full cold/warm shell comparisons. Historical measurements are in the consolidated study.

Use [qualification](../qualification/README.md) for regression/component tests. All retained measurement records live under this directory. Archived paths describe their old locations. Do not resume a cancelled study or infer current jobs from historical logs.

- [Observe strengths microbenchmarks](observe-strengths-microbench/README.md): actual shell workloads, explicit overhead stresses and controls, three scales, deterministic edit episodes and independent native-output validation. See its own status/report for completion; do not pool it with application benchmarks.
