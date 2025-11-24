TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt
export IN="$TOP/evaluation/microbenchmarks/eager/inputs/pg-min"

sleep 0.01
time ./scripts/eager.sh > output.txt
sha256sum output.txt