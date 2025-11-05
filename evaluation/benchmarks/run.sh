#!/bin/bash
cd "$(dirname "$0")" || exit 1

BENCHMARKS=("covid" "dpt" "file-mod" "nginx-analysis" "nlp-uppercase" "nlp-ngrams" "poet" "unixfun" "weather" "word-freq")
SIZES=("min" "min" "small" "small" "small" "small" "small" "small" "small" "small")
MODES=("" "" "" "" "" "" "" "" "" "")

rm -rf ../results
mkdir -p ../results

for i in "${!BENCHMARKS[@]}"; do
    benchmark="${BENCHMARKS[$i]}"
    size="${SIZES[$i]}"
    mode="${MODES[$i]}"

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
