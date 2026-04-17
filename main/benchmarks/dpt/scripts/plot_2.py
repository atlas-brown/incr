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

# --- Compute summary stats ---
glyphs = []
avg_confs = []
counts = []

for g, confs in glyph_confidences.items():
    glyphs.append(g)
    avg_confs.append(sum(confs) / len(confs))
    counts.append(len(confs))

glyphs, avg_confs, counts = zip(*sorted(zip(glyphs, avg_confs, counts), key=lambda x: x[1], reverse=True))

glyph_to_x = {g: i for i, g in enumerate(sorted(glyph_confidences.keys()))}
x_vals = [glyph_to_x[g] for g, _, _ in image_data]
y_vals = [c for _, c, _ in image_data]
labels = [img for _, _, img in image_data]
