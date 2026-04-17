# DPT Benchmark: Min-Mode Fix

## Problem

The `dpt` benchmark scripts (`dpt_1.sh` through `dpt_5e.sh`) unconditionally downloaded the full
`dpt.zip` dataset (~hundreds of images) from the internet on every run, regardless of whether
`--size min` was passed. This meant:

- `--size min` and `--size small` were functionally identical to `--size full` on first run.
- `inputs/dpt.min/dpt/` ended up containing the full downloaded dataset.
- There was no true "min" mode for quick testing.

The root cause: `fetch.sh --min` copied `min_inputs/dpt.min/pl-06-P_F-A_N-1.png` (a PNG medical
image) into `inputs/dpt.min/`, but scripts appended `/dpt` to `$IMG_DIR` and looked for `*.jpg`.
Since no JPEGs existed there, scripts always fell through to the `wget` download path.

The correct min JPEG inputs already existed in `min_inputs/jpg.min/jpg/` (5 JPEG photos) but were
never wired up.

---

## Changes

### 1. `fetch.sh` — min mode

**Before:** Copied `min_inputs/dpt.min/pl-06-P_F-A_N-1.png` (wrong format, wrong directory) into
`inputs/dpt.min/`.

**After:** For `--min`, creates two directories:
- `inputs/dpt.min/dpt.ref/` — permanent reference copy of 2 bundled JPEGs from
  `min_inputs/jpg.min/jpg/`. Never modified by scripts. Survives `clean.sh`.
- `inputs/dpt.min/dpt/` — initial working copy (seeded from `dpt.ref/`).

```bash
if [[ "$size" == "min" ]]; then
    if ! ls "$min_dir/dpt.ref"/*.jpg &>/dev/null 2>&1; then
        mkdir -p "$min_dir/dpt.ref"
        ls "${BENCHMARK_DIR}/min_inputs/jpg.min/jpg/"*.jpg | sort | head -1 | \
            xargs -I{} cp {} "$min_dir/dpt.ref/"
        echo "Min reference images prepared ($(ls "$min_dir/dpt.ref/"*.jpg | wc -l) images)."
    fi
    mkdir -p "$min_dir/dpt"
    cp "$min_dir/dpt.ref/"*.jpg "$min_dir/dpt/"
    echo "Min working images ready ($(ls "$min_dir/dpt/"*.jpg | wc -l) images)."
fi
```

The idempotency check only guards the one-time population of `dpt.ref/`. The `dpt/` working copy
is always refreshed from `dpt.ref/` — this handles the case where `clean.sh` removed `dpt/` but
left `dpt.ref/` intact.

To change the number of min images, adjust `head -1`.

### 2. `fetch.sh` — small mode

**Before:** Downloaded `pl-06-P_F-A_N-20250401T083751Z-001.zip` (PNGs) which scripts never used.

**After:** Downloads `dpt.zip`, keeps the first 10 JPEGs in `inputs/dpt.small/dpt/`. Scripts for
small/full mode still download `dpt.zip` themselves (unchanged), so this pre-fetch primarily
serves as future groundwork. The 10-image subset can be used once scripts gain a small-mode branch.

### 3. All 10 benchmark scripts — explicit min/non-min branch

**Before:** Every script unconditionally ran:
```bash
wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
unzip -o images.zip -d "$IMG_DIR"
rm images.zip
```

**After:** Scripts branch on `$RUN_SIZE` (which `run.sh` now exports):

```bash
if [[ "$RUN_SIZE" == "min" ]]; then
    cp "${IMG_DIR%dpt}dpt.ref"/*.jpg "$IMG_DIR/"
else
    wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
    unzip -o images.zip -d "$IMG_DIR"
    rm images.zip
fi
```

**Path expression explained:** After scripts do `IMG_DIR="$IMG_DIR/dpt"`, the path ends in
`.../dpt.min/dpt`. `${IMG_DIR%dpt}` strips the trailing `dpt`, giving `.../dpt.min/`. Appending
`dpt.ref` yields `.../dpt.min/dpt.ref`. The `%` operator strips from the right only, so the
`/benchmarks/dpt/` segment in the path is unaffected.

**Semantics:** Copying from `dpt.ref/` mirrors `unzip -o` exactly — it overwrites the working
directory with clean originals at the start of every script. This is important because scripts run
sequentially: `dpt_1.sh` runs `mogrify` (modifying `dpt/` in-place), then `dpt_2.sh` starts and
must restore the originals before processing.

#### `dpt_1.sh` specifically (has `mogrify`)

`mogrify -resize 1024x1024\> "$IMG_DIR"/*.jpg` is placed **outside** the if/else so it runs in
both modes — on the fresh copies from `dpt.ref/` in min mode, and on the freshly-unzipped images
in full/small mode:

```bash
if [[ "$RUN_SIZE" == "min" ]]; then
    cp "${IMG_DIR%dpt}dpt.ref"/*.jpg "$IMG_DIR/"
else
    wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
    unzip -o images.zip -d "$IMG_DIR"
    rm images.zip
fi
mogrify -resize 1024x1024\> "$IMG_DIR"/*.jpg
```

### 4. `run.sh` — export `RUN_SIZE`

Added `export RUN_SIZE` so the variable is visible to child bash processes running the scripts.
Place it alongside the other exports after `parse_benchmark_run_sh_args`:

```bash
export IMG_DIR="$INPUT_DIR/dpt${suffix}"
export RUN_SIZE          # <-- added
export OUTPUT_DIR
```

### 5. `clean.sh` — preserve `dpt.ref`

**Before:**
```bash
rm -rf inputs/dpt.min inputs/dpt.small inputs/dpt.full
```
This wiped `inputs/dpt.min/dpt.ref/` before every run, causing scripts to fail when copying from
the reference directory.

**After:**
```bash
rm -rf inputs/dpt.min/dpt inputs/dpt.small inputs/dpt.full
```
Only the working `dpt/` subdirectory is removed. `dpt.ref/` survives across runs. `dpt.small/`
and `dpt.full/` are cleaned fully since they have no reference directory.

---

## Expected workflow

```bash
# One-time setup (creates dpt.ref + installs deps)
bash evaluation/benchmarks/dpt/setup.sh --min

# Run benchmark in min mode (clean.sh removes dpt/ but not dpt.ref/)
bash evaluation/benchmarks/dpt/run.sh --size min --mode bash
```

On each script execution (min mode):
1. `cp dpt.ref/*.jpg dpt/` — restores 2 original JPEGs into working dir
2. (`mogrify` resizes them if `dpt_1.sh`)
3. Processing pipeline runs on the 2 images

---

## Files changed

| File | Change |
|------|--------|
| `fetch.sh` | min: create `dpt.ref/` + `dpt/` from `jpg.min/jpg/`; small: pre-fetch 10 images from dpt.zip |
| `scripts/dpt_1.sh` | `if RUN_SIZE==min: cp from dpt.ref` else `wget+unzip`; `mogrify` outside if/else |
| `scripts/dpt_2.sh` | `if RUN_SIZE==min: cp from dpt.ref` else `wget+unzip` |
| `scripts/dpt_3a.sh` | same |
| `scripts/dpt_3b.sh` | same |
| `scripts/dpt_4.sh` | same |
| `scripts/dpt_5a.sh` | same |
| `scripts/dpt_5b.sh` | same |
| `scripts/dpt_5c.sh` | same |
| `scripts/dpt_5d.sh` | same |
| `scripts/dpt_5e.sh` | same |
| `run.sh` | add `export RUN_SIZE` |
| `clean.sh` | `rm -rf inputs/dpt.min/dpt` (not the whole `dpt.min/`) |

---

## Notes

- The `min_inputs/dpt.min/pl-06-P_F-A_N-1.png` file (PNG medical image) is no longer used by
  `fetch.sh`. It can be removed from `min_inputs/` to avoid confusion, but doing so is not
  strictly required.
- The `min_inputs/jpg.min/jpg/` directory contains 5 JPEG photos; currently only 1 is used
  (`head -1` in `fetch.sh`). Adjust as needed.
- `$MODE` (uppercase) used in output filenames (`db.$MODE.txt`) is a pre-existing variable that
  comes from `run_lib.sh`'s `export mode` (lowercase). This produces filenames like `db..txt`
  with an empty MODE field. This is unchanged from the original scripts on both branches.
