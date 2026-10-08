# Qualification evidence

Start with [MEASUREMENTS.md](MEASUREMENTS.md) for the current aggregate status and
[AUDIT.md](../../AUDIT.md) for the semantics, fixes and limitations. The repository
work log is [QUALIFICATION_LOG.md](../../../QUALIFICATION_LOG.md).

Published evidence includes all final ordinary/DPT invocations (including invalid
main results), final regression and Bash differential results, dependency versions,
input/source/binary fingerprints, and the font-cache fixture diagnosis.
`published-code.json` maps the pushed commits to the exact measured source hashes.

The native Bash printf clock-boundary diagnostic is preserved in `bash-final-v12`;
the isolated paired recheck is in `bash-v12-clock-recheck`. The combined
`bash-v12-qualified-summary.json` explicitly records that exception.

Intermediate attempts, dependency-install output and download logs remain local
and ignored. Historical references in FINDINGS.md and the work log may refer to
those local diagnostic files. Models, virtual environments, downloaded inputs,
caches and compiled binaries are not included in these results.
