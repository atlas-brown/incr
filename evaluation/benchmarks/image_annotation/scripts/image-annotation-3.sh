#!/bin/sh

mkdir -p "$OUT"

find "$IN" -type f -iname "*.jpg" | while read -r img; do
    title=$(llm -m "gpt-4o-mini" "Your only output should be a **single** small title for this image:" -a "$img" -o seed 0 -o temperature 0 < /dev/null)

    filename=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/ /_/g').jpg

    cp "$img" "$OUT/$filename"
done
