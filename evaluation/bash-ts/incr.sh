#!/bin/bash

__TOP=$(git rev-parse --show-toplevel)
export INCR_SHELL="$__TOP/evaluation/bash-ts/bash/bash"
cache="/tmp/cache"
mkdir -p "$cache"
$__TOP/incr.sh $@ "$cache" 
