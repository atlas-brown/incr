# Benchmark changes since the paper measurements

Reference: `evaluation/default_results/default_1..3`, fully present at `7339eeb`.
Mean timings reproduce 34.2117525× across 85 edits, maximum 373.2632197× and
69 faster/16 slower edits. Removing image annotation gives 79 edits and 29.9584704×.
The historical measurements do not include file-level input hashes; source history
and paper descriptions cannot establish exact input-byte identity retroactively.

## Intentional executable repairs retained

These repairs were explicitly documented in `7990ee6:qualification/AUDIT.md`,
under "Benchmark repairs". Bio's selection was generalized further in `8f3c769`.
They are preserved identically under Bash, original Incr and Incr Observe.

| Family | Change | Meaning for historical comparison |
|---|---|---|
| beginner | Version 13 uses `head -n 10`, replacing erroneous `head 10` | Fixes an unintended filename read. Versions 13 and 14 may now be equivalent; retain both and disclose this. |
| bio | First version selects the input list's first sample instead of hardcoding HG00421 | Supports minimum fixtures and restored historical sample lists. Record the list and order. |
| file-mod/music | Final version archives WAV files before gzip/encryption instead of previous-stage `.gz` files | Removes reliance on stale outputs from another version; changes the final archive payload intentionally. |
| spell | Versions 6/7 lowercase and sort the installed dictionary before `comm`, then remove the owned temporary | Fixes `comm` preconditions. Dictionary hash and locale are pinned; output differs from the historically erroneous program. |
| DPT | Versions 5c/5d/5e pass formatted classifications to plotters and call `python3 scripts/plot_N.py`; final plot is saved rather than shown | Only final stage 5e writes a PNG; earlier plotters intentionally parse/summarize. Avoids interactive blocking. Original plot-stage times are not directly equivalent. |

DPT's minimum-image branch and setup fixes in April 2026 are deliberate smoke-test
support. It does not change the non-minimum branch. The current study retains them.
Web search also received deliberate index/ngram fixes but is outside this matrix.

The other paper workload scripts (COVID, temperature weather, nginx, ngrams,
uppercase, poet, Unix game and word frequency) have no executable-source changes
in the diff from `7339eeb` to the current branch. Numerous setup/run/clean scripts
and bundled minimum fixtures changed; those are infrastructure changes, not
unchanged evidence of the historical dataset.

## Data/setup defects and ambiguity

- Historical timing-era bio `input_small.txt` contains three medium samples
  (HG00421, HG01941, NA18500). The study uses those three; the earlier 15-sample
  list remains reference material rather than a mandatory paper-size target.
- Poet and spell historical fetchers cap newly prepared inputs at 200/500 MiB.
  The study preserves those recipes using the small Gutenberg archive, rather
  than forcing the paper's possibly stale 3001/9001-book descriptions. Ngrams
  and uppercase merge whole books lexically through 100/200 MiB respectively.
  Every selected name, resulting file hash and archive hash is recorded.
- Beginner's legacy small fetch doubles an existing input again on every setup.
  This is an idempotence defect; the study always constructs its selected recipe
  from an immutable download and records the multiplier: three doublings for
  beginner and two for nginx (roughly 974/487 MiB).
- Generic full NLP/weather archives are 17.8/22.4 GB compressed. Selecting them
  blindly is unnecessary and can exhaust this machine. The study uses bounded
  selected extraction, not the generic full setup.
- File-mod's full fetch downloads images rather than music. Its paper recipe uses
  the first ten MP3s from each of two selected groups in the small playlist archive.
- DPT's full setup branch is commented out; the scripts independently fetch
  `dpt.zip`. For paper measurements the study preserves wget/unzip operations but
  replaces the remote URL with an explicitly recorded local HTTP fixture mirror.
  This removes external network variation and is a disclosed timing deviation.
- Word-frequency setup historically downloaded unrelated chess/dictionary inputs;
  only its selected text recipe is prepared here.

The commit record supports intentional workload fixes and deliberate input
reductions. It does not establish that all later dataset differences were
accidental. Reproducibility defects are corrected in the study infrastructure;
intent is recorded only where the history provides evidence.

## Baselines and limits

Original Incr is pinned to `4b8e5dd`, the existing detached original/main checkout.
It includes post-measurement robustness changes relative to `7339eeb`; this is
explicitly a pinned original implementation comparison, not the exact historical
binary. Its runtime/parser/helpers remain unchanged. Current Observe runtime and
all binaries are separately hashed and frozen. Native Bash is the correctness
oracle. Invalid original results remain failures and are excluded from ratios.

Current Observe's final-output contract assumes deterministic application outputs
and no concurrent external mutations. This study contains sequential development
workloads. It does not validate the separate documented lock-sensitive warm replay
bug or claim arbitrary live/concurrent program equivalence.

## Full-size qualification finding

The first historical-size run stopped at original Incr music version 5.
`full-music-diagnostic-01` reproduced it: OpenSSL rejects the generated
`all_wavs.tar.enc` with `bad decrypt`. Bash and Observe pass that same version.
The original runtime remains pinned and unchanged; its invalid sample is excluded
from timing ratios, and the remainder of that invalid original sequence is not
measured against a corrupted state. The diagnostic directory retains the
validator traceback, encrypted-file size/hash, and benchmark stderr. This issue
was absent on the tiny minimum input, demonstrating why full-size correctness
validation is required too.

The next evaluation explicitly continues to other sequences after a failed
sequence. It preserves failed-family inputs and never reports an incomplete
schedule as a fully qualified comparison.

The user subsequently authorized minimal baseline repairs. The archived patch in
`reference/original-minimal-fixes.patch` bypasses memoization for `openssl enc`,
identically in both runtimes. A 128 MiB direct probe reproduced corruption in both
unfixed implementations and passes cold/warm encryption after the fix. New runs
identify this repaired baseline separately; the historical results are unchanged.


## Framework cache namespace isolation

The measurement environment puts Matplotlib and PyTorch compiler caches under
fixture/config rather than TMPDIR, identically for Bash, original Incr and Observe.
This prevents independent framework stages from changing a directory the other
stage observed. Model weights and workload programs are unchanged; the cache
locations and all environment values are recorded per sequence. Both cache
namespaces are recreated with each fixture and removed after measurement and
validation. The import-only torch-temp-interference-01 probe reproduces and fixes
the cross-framework invalidation without relaxing metadata dependency checks.

## Opt-in live image study repair

The separate `image-annotation-api-2026-10-16` study found that different images can receive identical `gpt-4o-mini` titles, causing the original shell scripts to overwrite earlier output images. All seven versions now prefix output filenames with the input image basename using the same shell assignment. A deterministic identical-title regression covers all seven versions. This is a workload correctness repair shared by Bash/original/Observe, with no runtime optimization or annotation. The live study separately labels its image-payload validation because fresh generated titles are nondeterministic; it is excluded from the unchanged deterministic historical manifest.
