#!/bin/bash
cd "$(dirname "$0")" || exit 1

BENCHMARKS=("covid" "nginx-analysis" "ngrams" "unixfun" "weather" "weather" "word-freq")
MODES=("" "" "" "" "" "tuft-weather" "")
SIZES=("small" "small" "small" "small" "small" "small" "small")

rm -rf ../results
mkdir -p ../results

for i in "${!BENCHMARKS[@]}"; do
    benchmark="${BENCHMARKS[$i]}"
    mode="${MODES[$i]}"
    size="${SIZES[$i]}"

    echo "Running $benchmark '$mode' $size"
    bash "$benchmark/clean.sh"
    sleep 0.01

    cd "$benchmark"
    if [[ "$mode" == "" ]]; then
        bash execute.sh "--$size"
    else
        bash execute.sh "$mode" "--$size"
    fi
    cd "$(dirname "$0")"
    sleep 0.01

    cp "$benchmark/outputs/timing.csv" "../results/$benchmark-timing.csv"
done