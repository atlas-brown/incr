#!/bin/bash
cd $(dirname "$0")
export PYTHONPATH="$(pwd):$PYTHONPATH"

INPUT_URL='https://atlas.cs.brown.edu/data/dummy/1M.txt'

mkdir -p inputs
mkdir -p outputs
# Download the input file only if missing
if [ ! -f inputs/in.txt ]; then
  echo "[demo] Downloading input (1 MB)…"
  curl -sf "${INPUT_URL}" -o inputs/in.txt || { echo "Download failed"; exit 1; }
fi

TIMEFORMAT=%R

echo "[demo] Running normal processing…"
elapsed=$({ time cat inputs/in.txt | grep '\(.\).*\1\(.\).*\2\(.\).*\3\(.\).*\4\(.\).*\5\(.\).*\6' | tr A-Z a-z > outputs/out.txt; } 2>&1)
echo "[output] Normal execution time: $elapsed seconds"

echo "[demo] Running with result persistence and fault injection " >&2
random_id=$(uuidgen)
elapsed=$({ time cat inputs/in.txt | grep '\(.\).*\1\(.\).*\2\(.\).*\3\(.\).*\4\(.\).*\5\(.\).*\6' | ./tee-cache/target/release/tee-cache ${random_id} | python -m frac byte-kill --bytes 500 --cmd "tr A-Z a-z" 2>/dev/null >outputs/persist-out.txt; } 2>&1)
echo "[output] Execution time: $elapsed seconds"

echo "[demo] Rerunning partial computation..."
elapsed=$({ time cat /tmp/cache_${random_id}.tmp | tr A-Z a-z >outputs/partial-recompute-out.txt; } 2>&1)
echo "[output] Partial computation time: $elapsed seconds"

echo "[demo] comparing partial-recompute-out.txt with out.txt..."
if diff outputs/partial-recompute-out.txt outputs/out.txt; then
  echo "[output] correct!"
else
  echo "[output] differences found."
fi