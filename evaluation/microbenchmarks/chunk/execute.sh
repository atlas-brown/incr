# sudo rm -rf "../../../cache"
rm -f out.txt
TOP=$(git rev-parse --show-toplevel)
export IN="$TOP/evaluation/microbenchmarks/chunk/inputs/pg-min"

sleep 0.01
time ./scripts/chunk.sh > out.txt
sha256sum out.txt