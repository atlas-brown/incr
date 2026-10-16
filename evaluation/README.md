# Workload sources

`benchmarks/*/scripts/` contains the maintained workload programs; `min_inputs/` contains only deterministic minimum seed fixtures. The maintained Bash runner installs its checksum-verified official corpus explicitly under `qualification/.tools/`. Do not instrument or mutate these sources for measurement.

Use [the study harness](../studies/paper-size-benchmarks/README.md) for all benchmark preparation, execution and output validation. All historical/current statistics from both repos live in [the consolidated study](../studies/evaluation-checkpoint-2026-10-16/README.md). Superseded per-family launchers, generated datasets, caches and plots were removed. DPT models are downloaded only by the explicit setup command documented with the harness.
