#!/bin/bash
cd "$(dirname "$0")" || exit 1

BENCHMARKS=("covid" "inference" "nginx-analysis" "nlp-bigrams" "unixfun" "weather" "word-freq")
MODES=("" "" "" "" "" "" "")
SIZES=("min" "min" "small" "small" "small" "small" "small")

rm -rf ../results
mkdir -p ../results

for i in "${!BENCHMARKS[@]}"; do
    benchmark="${BENCHMARKS[$i]}"
    mode="${MODES[$i]}"
    size="${SIZES[$i]}"

    echo "Running $benchmark '$mode' $size"
    sudo bash "./$benchmark/clean.sh"
    sleep 0.01

    if [[ "$mode" == "" ]]; then
        bash "./$benchmark/execute.sh" "--$size"
    else
        bash "./$benchmark/execute.sh" "$mode" "--$size"
    fi
    sleep 0.01

    if [[ "$mode" == "" ]]; then
        cp "./$benchmark/outputs/timing.csv" "../results/$benchmark-timing.csv"
    else
        cp "./$benchmark/outputs/timing.csv" "../results/$benchmark-$mode-timing.csv"
    fi
done