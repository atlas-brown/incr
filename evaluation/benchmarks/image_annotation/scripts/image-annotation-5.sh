#!/bin/sh

IN=$1
OUT=$2
mkdir -p "$OUT"

find "$IN" -type f -iname "*.jpg" | while read -r img; do
    title=$(llm -m "gpt-4o-mini" "Your only output should be a **single** small title for this image:" -a "$img" -o seed 0 -o temperature 0 < /dev/null)

    base=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g' | sed 's/[^a-z0-9_-]//g')
    filename="${base}.jpg"

    cp "$img" "$OUT/$filename"
done
