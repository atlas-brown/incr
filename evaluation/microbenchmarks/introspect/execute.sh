TOP=$(git rev-parse --show-toplevel)
# sudo rm -rf "$TOP/cache"
rm -f output.txt
export IN="$TOP/evaluation/microbenchmarks/introspect/inputs/pg-min/manif12.txt"

sleep 0.01
time ./scripts/introspect.sh > output.txt
sha256sum output.txt