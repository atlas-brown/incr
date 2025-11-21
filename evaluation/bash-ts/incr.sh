#!/bin/bash

__TOP=$(git rev-parse --show-toplevel)
export INCR_SHELL=$__TOP/evaluation/bash-ts/bash/bash
$__TOP/incr.sh "$@" "$__TOP/evaluation/bash-ts/cache"
