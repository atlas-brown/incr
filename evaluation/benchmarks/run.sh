#!/bin/bash
cd "$(dirname "$0")" || exit 1

BENCHMARKS=("covid" "nginx-analysis" "ngrams" "unixfun" "weather" "weather" "word-freq")
MODES=("" "" "" "" "" "tuft-weather" "")
SIZES=("small" "small" "small" "small" "small" "small" "small")

rm -rf ../evaluation/results
mkdir -p ../evaluation/results

for i in "${!BENCHMARKS[@]}"; do
    benchmark="${BENCHMARKS[$i]}"
    mode="${MODES[$i]}"
    size="${SIZES[$i]}"

    echo "Running $benchmark '$mode' $size"
    bash "$benchmark/clean.sh"
    sleep 0.01

    if [[ "$mode" == "" ]]; then
        bash "$benchmark/execute.sh" "--$size"
    else
        bash "$benchmark/execute.sh" "$mode" "--$size"
    fi
    sleep 0.01

    break
    #cp "$benchmark/outputs/timing.csv" "../evaluation/results/$benchmark-timing.csv"
done