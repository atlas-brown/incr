#!/bin/bash
# setup.sh: idempotently install dependencies and fetch data for the file-mod benchmark.
# Usage: setup.sh [--min|--small|--full]
set -euo pipefail
cd "$(dirname "$0")" || exit 1

TOP=$(git rev-parse --show-toplevel)
BENCHMARK_DIR="$TOP/evaluation/benchmarks/file-mod"
INPUT_DIR="$BENCHMARK_DIR/inputs"

size=small
for arg in "$@"; do
    case "$arg" in
        --min)   size=min ;;
        --small) size=small ;;
        --full)  size=full ;;
    esac
done

echo "[setup] file-mod: installing dependencies (ffmpeg, openssl)..."
# Note: file-mod scripts only use ffmpeg and openssl.
# The existing install.sh installs a heavy LLM/torch stack that isn't needed here.
if ! command -v ffmpeg &>/dev/null; then
    sudo apt-get install -y ffmpeg 2>/dev/null || true
fi

mkdir -p "$INPUT_DIR"

if [[ "$size" == "min" ]]; then
    target_dir="$INPUT_DIR/songs.min"
    if [[ ! -d "$target_dir" ]]; then
        echo "[setup] file-mod: generating minimal MP3 inputs using ffmpeg..."
        mkdir -p "$target_dir"
        # Generate short silent MP3 files for testing
        for i in 1 2 3; do
            ffmpeg -y -f lavfi -i "anullsrc=r=22050:cl=mono" -t 1 \
                -codec:a libmp3lame -b:a 32k \
                "$target_dir/track${i}.mp3" 2>/dev/null
        done
    fi
else
    echo "[setup] file-mod: fetching $size inputs..."
    bash "$BENCHMARK_DIR/fetch.sh" "--$size"
    # fetch.sh --small puts data in inputs/songs.small; fix for .min already done above
fi

echo "[setup] file-mod: done."
