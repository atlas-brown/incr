#!/bin/bash

script=$1
cache_dir=$2
TOP=$(git rev-parse --show-toplevel)
TRY_PATH="$TOP/src/scripts/try.sh"
tempfile=$(mktemp "$(dirname $script)/incr_script.XXXXXXXX.sh")

[ -z "$script" ] && echo "Usage: $0 <script> <cache_dir>" && exit 1
[ -z "$cache_dir" ] && echo "Usage: $0 <script> <cache_dir>" && exit 1

echo "inserting: $tempfile"
python3 ${TOP}/src/scripts/insert.py --sys-path ${TOP}/target/release/incr --try $TRY_PATH --cache $2 "$1" > "$tempfile"
bash $tempfile
