#!/bin/bash
# Summarize default vs observe results (no Python deps)
cd "$(dirname "$0")/.." || exit 1
D=run_results/default
O=run_results/observe
echo "Benchmark           default    observe    ratio"
echo "------------------------------------------------"
for f in "$D"/*-time.csv; do
  b=$(basename "$f" -time.csv)
  [ -f "$O/$b-time.csv" ] || continue
  d=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$f")
  o=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$O/$b-time.csv")
  r=$(awk "BEGIN {print ($d/$o)}" 2>/dev/null || echo "0")
  printf "%-20s %8.3f  %8.3f  %6.2fx\n" "$b" "$d" "$o" "$r"
done
echo "------------------------------------------------"
dt=0
ot=0
for f in "$D"/*-time.csv; do
  v=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$f")
  dt=$(echo "$dt + $v" | bc)
done
for f in "$O"/*-time.csv; do
  v=$(awk -F, 'NR>1 {s+=$3} END {print s+0}' "$f")
  ot=$(echo "$ot + $v" | bc)
done
rt=$(awk "BEGIN {print ($dt/$ot)}" 2>/dev/null || echo "0")
printf "%-20s %8.3f  %8.3f  %6.2fx\n" "TOTAL" "$dt" "$ot" "$rt"
