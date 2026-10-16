# Fresh Observe reproduction

This study uses a new owned `.work`, fixtures and caches on a clean pushed Incr
and Observe checkpoint. It reuses the committed historical study harness through
`INCR_BENCH_STUDY`; each measurement run freezes its scripts, binaries and harness.
Existing shared model files are verified and retained. Annotations stay off.

`reproduce.py` serially prepares and measures all 13 historical families at the
historical-size profile (828 invocations, three paired repetitions), audits that
cohort, then prepares and measures the full web-search and weather-Tufte workloads
as a separate cohort (45 invocations, three paired repetitions). Only image
annotation requiring an OpenAI API key is excluded. Supplemental inputs are not
prepared while historical measurements run. Resource failures or output
mismatches stop the controller and preserve the failed evidence.

Before launch, `results/checkpoint.json` must pin both clean pushed Git heads,
the qualified binary hashes, original baseline and reviewed patch, and hashes of
the committed qualification/targeted review and evidence catalog. The launcher
must independently verify remote heads. `--check` verifies those pins without
preparing inputs or measuring anything. Execution must run as the main process of
`incr-bench-study.service`, with user lingering enabled and KillMode=control-group.

The workspace budget is 32 GiB with an 8 GiB reserve. Preparation and measurement
are separate; owned inputs are released only after their family's complete three
pairs. The full supplied Wikipedia corpus/index and seeded 27-city, 30-year
weather generator are required. No prior fixture/cache or minimum input is
substituted for the full workload. Peak disk/cache and GNU time resources, exact
native comparisons, every sample, source/input provenance and failures are saved.

Inspect `results/controller.json`, `results/logs/reproduction.log`, and the live
`incr-bench-study.service`. The monitor timer follows the active measurement
cohort. Closing VS Code or logging out does not stop a lingering systemd user
service; the machine must remain running. Plans and preflight success do not
prove a live launch: verify the actual MainPID, phase, run heartbeat and monitor.

Implementation code is installed here before the checkpoint push. Input
preparation and measurements start only after the final gates, pushes and
preflight succeed. Live pins/status are ignored generated evidence; no full
reproduction results are claimed by this README.
