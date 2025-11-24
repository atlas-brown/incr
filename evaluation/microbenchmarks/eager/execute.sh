# sudo rm -rf "../../../cache"
rm -f out.txt
TOP=$(git rev-parse --show-toplevel)
export IN="$TOP/evaluation/microbenchmarks/eager/inputs/pg-min"

sleep 0.01
time ./scripts/eager.sh > out.txt
sha256sum out.txt
# rm out.txt