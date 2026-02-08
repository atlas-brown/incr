#!/usr/bin/env python3

import sys
import re
from collections import defaultdict
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} predictions.txt", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]

# Data containers
glyph_confidences = defaultdict(list)
image_data = []

# Expected line format: g: <glyph> c: <confidence> <image_path>
line_re = re.compile(r"g:\s*(\S+)\s+c:\s*([0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+(\S+)")

with open(path) as f:
    for line in f:
        m = line_re.search(line)
        if not m:
            continue
        glyph, conf, img = m.groups()
        conf = float(conf)
        glyph_confidences[glyph].append(conf)
        image_data.append((glyph, conf, img))

if not glyph_confidences:
    print("No valid lines found.", file=sys.stderr)
    sys.exit(1)
