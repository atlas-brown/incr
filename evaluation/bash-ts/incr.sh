#!/bin/bash

__TOP=$(git rev-parse --show-toplevel)
if [[ "$1" == "./"* ]]; then
    $__TOP/incr.sh "$1" "$__TOP/evaluation/bash-ts/cache"
else
    bash $@
fi