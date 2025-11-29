TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt

export IN="$TOP/evaluation/microbenchmarks/group/inputs/pg-small"

sleep 0.01
time ./scripts/pipe.sh > output.txt
sha256sum output.txt

sleep 0.01
time ./scripts/group.sh > output.txt
sha256sum output.txt