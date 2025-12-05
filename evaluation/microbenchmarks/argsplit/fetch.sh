#!/bin/bash

TOP=$(git rev-parse --show-toplevel)
URL="https://atlas.cs.brown.edu/data"
BENCHMARK="argsplit"

input_dir="${TOP}/evaluation/microbenchmarks/${BENCHMARK}/inputs"
mkdir -p "$input_dir"

python3 gen_c.py
mv ./*.c "${input_dir}/"
