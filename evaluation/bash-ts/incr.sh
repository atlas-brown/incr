#!/bin/bash

top=/home/vagozino/incr
export INCR_SHELL="$top/evaluation/bash-ts/bash/bash"
export THIS_SH="$top/evaluation/bash-ts/incr.sh"
cache="/tmp/cache"
mkdir -p "$cache"
$top/incr.sh "$@"
