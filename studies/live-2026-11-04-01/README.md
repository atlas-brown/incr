# Isolated live-policy replication

**Complete:** all 828 deterministic application, 63 image API and 2,754 synthetic invocations passed their output audits. Owned workspaces and temporary API credentials were removed. The initial automatic publication stopped on significant whitespace in copied patch files; the patch bytes were preserved and the repository attribute fixed before manual publication. See `completion.json` for the verification receipt.

Portable tables, historical comparisons and PDF/PNG figures are in the sibling paper repository at [data/live-2026-11-04](../../../incr-formalization/paper/data/live-2026-11-04/README.md) and [figs/live-2026-11-04](../../../incr-formalization/paper/figs/live-2026-11-04/README.md). Historical final-policy results remain unchanged.

This campaign measures the historical application and synthetic scope using Observe's live effect policy. Original evidence is unchanged. The API image cohort is separate and validates image payloads, not generated filenames.

- Scope: 828 deterministic application, 2,754 synthetic, 63 image invocations; three paired repetitions.
- Smoke: minimum word frequency, tiny synthetic diagnostics, minimum image sequence. Smoke samples are excluded from final measurements.
- Service: `live-2026-11-04-01.service`; user lingering is enabled. Window closure is safe; host shutdown does not resume the job.
- Progress: `results/controller-run/status.json`; stage logs are beside it. Smoke status is under `results/controller-smoke/`.
- Stop: `systemctl --user stop live-2026-11-04-01.service`.
- Status: `systemctl --user status live-2026-11-04-01.service`.
- Results: application `results/paper-*`; sibling `live-2026-11-04-01-micro/measurements/full-live` and `live-2026-11-04-01-image/results/paper-image`.
- Completion: verified archives and summaries under `completed-evidence/`, followed by owned workspace cleanup and a non-force commit/push. `results/controller-run/publication.json` records remote verification. Publication stops if the repository or implementation changed during measurement.

Runtime source is unchanged. Harness changes expose policy, enforce cross-study locking and verify effective policy. The monitor respects image payload comparison. Git patch comparison pins hash abbreviation to avoid a false baseline mismatch. Synthetic zero-cache samples retain warnings; a separate matching diagnostic establishes backend execution without claiming reuse. Dependencies were reconstructed from recorded primary versions; exact newly installed package/tool versions are saved per run. New binaries/host conditions are a fresh cohort, not a bit-identical reconstruction of historical timings.
