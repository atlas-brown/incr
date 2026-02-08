TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt

INPUT_DIRECTORY="$TOP/evaluation/microbenchmarks/introspect/inputs/pg-small"
INPUT_FILE="$INPUT_DIRECTORY/data_chunk_0.txt"
IN="$INPUT_DIRECTORY/book.txt"
export IN="$IN"

cp "$INPUT_FILE" "$IN"
sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

echo "The quick brown fox jumped over the lazy dog." >> "$IN"
sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

echo "The quick brown fox jumped over the lazy dog." >> "$IN"
sleep 0.01
time ./scripts/chunk.sh > output.txt
sha256sum output.txt

rm -f "$IN"