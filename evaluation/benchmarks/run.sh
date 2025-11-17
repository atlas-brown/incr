#!/bin/bash
cd "$(dirname "$0")" || exit 1

BENCHMARKS=(
    "beginner"
    "bio"
    "covid"
    "dpt"
    "file-mod"
    "image-annotation"
    "nginx-analysis"
    "nlp-uppercase"
    "nlp-ngrams"
    "poet"
    "spell"
    "unixfun"
    "weather"
    "word-freq"
)
SIZES=(
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
    "small"
)

rm -rf ../results
mkdir -p ../results

for i in "${!BENCHMARKS[@]}"; do
    benchmark="${BENCHMARKS[$i]}"
    size="${SIZES[$i]}"
    mode=""

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
        cp "./$benchmark/outputs/timing.csv" "../results/$benchmark-time.csv"
        du -sb "./$benchmark/cache" > "../results/$benchmark-size.txt"
        rm -rf "./$benchmark/cache"
    else
        cp "./$benchmark/outputs/timing.csv" "../results/$benchmark-time.csv"
        du -sb "./$benchmark/cache" > "../results/$benchmark-size.txt"
        rm -rf "./$benchmark/cache"
    fi
done
