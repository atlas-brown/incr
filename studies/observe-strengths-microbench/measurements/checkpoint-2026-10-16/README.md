# Interim synthetic microbenchmark results

Immutable snapshot of 1920 completed, individually validated timings out of 2,754 planned. This is partial evidence, not a completed study or final independent audit. The systemd worker continues writing `../final-01/`; it does not modify this checkpoint.

`samples.jsonl` preserves every completed sample including validation fingerprints, resource statistics, output manifests and cache statistics. `timings.csv` is a compact projection of exactly the same samples. Configuration, binary/source provenance and frozen runtime source archives are included. `checkpoint.json` records capture time, scope and SHA256 hashes. In-flight samples are excluded. Do not pool this duplicate snapshot with the eventual final results.
