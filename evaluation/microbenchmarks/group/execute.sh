TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt

export IN="$TOP/evaluation/microbenchmarks/group/inputs/pg-small/data_chunk_0.txt"

sudo rm -rf "$TOP/cache"

sleep 0.01
time ./scripts/pipe.sh > output.txt
sha256sum output.txt
sleep 0.01
time ./scripts/pipe.sh > output.txt
sha256sum output.txt

sudo rm -rf "$TOP/cache"

sleep 0.01
time ./scripts/incr_pipe.sh > output.txt
sha256sum output.txt
sleep 0.01
time ./scripts/incr_pipe.sh > output.txt
sha256sum output.txt

sudo rm -rf "$TOP/cache"

sleep 0.01
time ./scripts/incr_group.sh > output.txt
sha256sum output.txt
sleep 0.01
time ./scripts/incr_group.sh > output.txt
sha256sum output.txt

sudo rm -rf "$TOP/cache"

sleep 0.01
time ./scripts/incr_disable.sh > output.txt
sha256sum output.txt
sleep 0.01
time ./scripts/incr_disable > output.txt
sha256sum output.txt