#!/usr/bin/env bash
set -e
read -r limit < limit.txt
i=0
total=0
while [ "$i" -lt "$((limit * 1000))" ]; do
 total=$((total + i))
 i=$((i + 1))
done
printf "%s\n" "$total"
