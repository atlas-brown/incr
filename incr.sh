#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
tempfile=$(mktemp)
python3 ${TOP}/src/scripts/insert.py --sys-path ${TOP}/target/release/incr "$1" > "$tempfile"
bash $tempfile