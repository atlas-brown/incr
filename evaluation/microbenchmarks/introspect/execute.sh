TOP=$(git rev-parse --show-toplevel)
sudo rm -rf "$TOP/cache"
rm -f output.txt

INPUT_DIRECTORY="$TOP/evaluation/microbenchmarks/introspect/inputs/pg-small"
IN="$INPUT_DIRECTORY/book.txt"
export IN="$IN"

for chunk in "$INPUT_DIRECTORY"/data_chunk_*.txt; do
    echo "Running microbenchmark with $chunk"
    cp "$chunk" "$IN"
    sleep 0.01
    time ./scripts/introspect.sh > output.txt
    sha256sum output.txt
done

rm -f "$IN"