TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt
export IN="$TOP/evaluation/microbenchmarks/chunk/inputs/pg-min"

sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

rm -- "$IN"/*_dup.*
file=$(find "$IN" -maxdepth 1 -type f -printf '%f\n' | sort | head -n1)
duplicated="$IN/${file%.*}_dup.${file##*.}"
cp "$IN/$file" "$duplicated"

sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

rm -f "$duplicated"