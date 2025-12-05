#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
inputs="${TOP}/evaluation/microbenchmarks/argsplit/inputs"
cd "$TOP/evaluation/microbenchmarks/argsplit" || exit 1

PROGRAM="${TOP}/target/release/incr"
# PROGRAM=""

gcc -O3 -flto -march=native -c "$inputs"/*.c # Long-running splittable command
sha256sum ./*.o # Short-running splittable command
