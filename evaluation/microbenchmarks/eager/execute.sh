# sudo rm -rf "../../../cache"
rm -f output.txt
TOP=$(git rev-parse --show-toplevel)
export IN="$TOP/evaluation/microbenchmarks/eager/inputs/pg-min"

sleep 0.01
time ./scripts/eager.sh > output.txt
sha256sum output.txt