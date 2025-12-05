#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
inputs="${TOP}/evaluation/microbenchmarks/argsplit/inputs"
cd "$TOP/evaluation/microbenchmarks/argsplit" || exit 1

PROGRAM="${TOP}/target/release/incr"
# PROGRAM=""

gcc -O3 -flto -march=native -c "$inputs"/file000.c
gcc -O3 -flto -march=native -c "$inputs"/file001.c
gcc -O3 -flto -march=native -c "$inputs"/file002.c
gcc -O3 -flto -march=native -c "$inputs"/file003.c
gcc -O3 -flto -march=native -c "$inputs"/file004.c

sha256sum ./file000.o
sha256sum ./file001.o
sha256sum ./file002.o
sha256sum ./file003.o
