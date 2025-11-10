#!/bin/bash
# tag: segment-classify-index sequential

cd "$(dirname "$0")/.." || exit 1

wget "https://atlas-group.cs.brown.edu/data/dpt/dpt.zip" -O images.zip
IMG_DIR=${:-images}
unzip images.zip -d "$IMG_DIR"

for img in $(find "$IMG_DIR" -type f -name '*.jpg' | sort); do
    cat "$img" | python3 scripts/segment.py |
    python3 scripts/classify.py "$img" |
    tee classifications.txt |
    awk -vi="$img" '{print "g:", $5, "c:", $6, i}' 
done | sort > db.txt

python plot.py classifications.txt
