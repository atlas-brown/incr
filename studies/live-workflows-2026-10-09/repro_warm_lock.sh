#!/usr/bin/env bash
# Known warm-cache counterexample, separate from the sixteen isolation examples.
# Exit 1 means cached behavior differs from native execution after lock release.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "$here/../.." && pwd)
mkdir -p "$here/.work"
work=$(mktemp -d "$here/.work/lock-replay.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT
cd "$work"
: > lock
attempt='exec 9>>lock; if flock --nonblock 9; then echo acquired; else echo busy; fi'
memo=("$root/target/release/incr" -b --effect-policy live --cache "$work/cache"
      --try "$root/src/scripts/try.sh" --observe "$root/../observe/target/release/observe"
      -- bash -c "$attempt")
held=$(flock --exclusive --close lock "${memo[@]}")
reference=$(bash -c "$attempt")
cached=$("${memo[@]}")
printf 'Held, cold Observe: %s\nReleased, native: %s\nReleased, warm Observe: %s\n' \
    "$held" "$reference" "$cached"
[[ $held == busy && $reference == acquired && $cached == "$reference" ]]
