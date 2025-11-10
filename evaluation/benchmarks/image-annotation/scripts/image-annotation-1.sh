#!/bin/sh

mkdir -p "$OUT"

find "$IN" -type f -iname "*.jpg" | while read -r img; do
    echo "found image: $img"
    title=$(llm -m "gpt-4o-mini" "Your only output should be a **single** small title for this image:" -a "$img" -o seed 0 -o temperature 0 < /dev/null)
    echo "generated title: $title"

    filename="${title}.${mode}.jpg"
    echo "filename: $filename"

    cp "$img" "$OUT/$filename"
done
