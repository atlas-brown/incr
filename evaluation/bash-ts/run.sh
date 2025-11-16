#!/bin/sh

cd "$(dirname "$0")" || exit 1
cd tests

# First, run tests with bash
export THIS_SH=bash
export BASH_TSTOUT=/tmp/tstout

# sh run-all > ../results.bash

# Then, run tests with incr
TOP=$(git rev-parse --show-toplevel)
export THIS_SH=$TOP/evaluation/bash-ts/incr.sh
export INCR_TSTOUT=/tmp/tstout

sh run-all > ../results.incr
