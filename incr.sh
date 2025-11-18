#!/bin/bash

script=$1
cache_dir=$2

incr_shell=${INCR_SHELL:-bash}

[ -z "$script" ] && echo "Usage: $0 <script> <cache_dir>" && exit 1
[ -z "$cache_dir" ] && echo "Usage: $0 <script> <cache_dir>" && exit 1

TOP=$(git rev-parse --show-toplevel)
TRY_PATH="$TOP/src/scripts/try.sh"
tempfile=$(mktemp "$(dirname $script)/incr_script.XXXXXXXX.sh")

# Ensure cleanup and preserve the right exit status.
rc=
cleanup() {
    # If we recorded the temp script's status, use it; otherwise use last command's.
    local st=${rc:-$?}
    rm -f "$tempfile"
    exit $st
}
trap cleanup EXIT INT TERM

python3 ${TOP}/src/scripts/insert.py --sys-path ${TOP}/target/release/incr --try $TRY_PATH --cache $2 "$1" > "$tempfile"
bash "$tempfile"
$incr_shell "$tempfile"
rc=$?
