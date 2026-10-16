# Detailed checkpoint evidence

The current gate is [CHECKPOINT.json](../CHECKPOINT.json); the readable interpretation is [RESULTS.md](../RESULTS.md). Earlier checkpoint documents and archives remain historical evidence.

`trusted-cache-2026-10-16-03/catalog.json` contains 198 independent study, diagnostic and Bash result groups with 24,105 archived files. `qualification-2026-10-16/catalog.json` adds four historical qualification groups with 6,687 files, including previously ignored records. Keep cohorts separate: failed, incomplete, exploratory and old-revision measurements are not final performance samples. A declared status inside an archived source file does not replace terminal validation.

Each group has a file catalog and ordered archive parts with byte sizes and SHA256. Concatenate the listed parts in order into one gzip archive, verify the combined bundle hash, then extract; verify members against the file catalog. Most groups have one `.tar.gz`; large groups have `.tar.gz.part-000`, etc. Every part is at most 80 MiB. Collection verified every member and every part. The exact primary collection script is preserved beside its catalog; `collect.py` includes the later qualification namespace support.

All timing, storage/resource, provenance, source snapshots, correctness logs and failure metadata are archived. Thirty-two large raw payload/link receipts in the primary catalog identify retained on-disk artifacts by size/hash or link target; large binary profiles are not duplicated in Git. Original evidence is not deleted. Two partial export attempts are documented by EXPORT_ATTEMPT_SIZE_LIMIT.json and EXPORT_ATTEMPT_PERMISSION.json; their generated partial archives remain ignored locally. The successful exports fixed archive splitting and read-only access to root-created profiling data.

The final targeted review, paired report and resource CSV are also directly accessible in `trusted-cache-2026-10-16-03/`. `cleanup.json` records subsequent removal of disposable old owned prepared inputs and scratch; models, frozen builds and result evidence are retained. Fresh reproduction evidence will be a new independent cohort.
