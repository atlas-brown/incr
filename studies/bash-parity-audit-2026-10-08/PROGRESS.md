# Final-policy clean qualification

- Supersedes the earlier live-policy study; old raw results and verification artifacts were removed. Historical evidence remains in git commit 4a772a4.
- Changed the binary effect-policy default from live to final. The Bash harness leaves INCR_EFFECT_POLICY unset, exercising the actual default.
- Removed both Rust target trees and frozen runtime snapshots before rebuilding. Each new case receives an empty private cache; only the new cold cache is retained for its warm run. Official Bash sources and parser prerequisites are preserved and verified.
- Full rerun completed: 83/83 cold and warm, 12,234/12,234 lines per phase; paper subset 10,282/10,282. Total 815.56 seconds.
- Rebuilt binary help verified `[default: final]` with INCR_EFFECT_POLICY removed. Added this prerequisite assertion to the maintained runner. Removed legacy Bash-only result directories under qualification/results as requested; unrelated benchmark evidence remains.
- Both 57-case policy regression suites and all 18 harness checks passed. Independent raw-record reanalysis found no missing captures, substantive differences, skip diagnostics, cold/warm variation, timeouts or survivors.
- Cache inventories verified empty before every cold execution. Final run produced 405 cold / 476 warm entries, retaining 378 metadata files across 36 groups.
- Final checks: all 29 Rust tests passed (28 regular plus the explicitly enabled ownership test), 18 harness tests passed, frozen-binary help confirmed final, and recorded runtime source hashes matched the working tree. Removed the generated frozen runtime snapshots after verification.
