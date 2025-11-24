TOP=$(git rev-parse --show-toplevel)
# sudo rm -rf "$TOP/cache"
rm -f output.txt
export IN="$TOP/evaluation/microbenchmarks/chunk/inputs/pg-small"
extra_file="$TOP/evaluation/microbenchmarks/chunk/inputs/pg-min/manif12.txt"

sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

rm -f -- "$IN"/*_prev.*
file=$(find "$IN" -maxdepth 1 -type f -printf '%f\n' | sort | head -n1)
previous="$IN/${file%.*}_prev.${file##*.}"
cp "$IN/$file" "$previous"
cat "$extra_file" >> "$IN/$file"

sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

mv "$previous" "$IN/$file"