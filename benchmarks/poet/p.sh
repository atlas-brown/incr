#!/bin/bash
# sort_genesis.sh
# Generate frequency, alphabetical, and rhyming word lists from the file "genesis"

# Input file
INPUT="genesis"

# Output files
FREQ_OUT="genesis.hist"
ALPHA_OUT="genesis.alpha"
RHYME_OUT="genesis.rhyme"

# 1. Sort by frequency
tr -sc 'A-Za-z' '\012' < "$INPUT" |
    sort | 
    uniq -c | 
    sort -nr > "$FREQ_OUT"

# 2. Sort by dictionary (alphabetical) order
tr -sc 'A-Za-z' '\012' < "$INPUT" | 
sort -u > "$ALPHA_OUT"

# 3. Sort by rhyming order (using rev)
tr -sc 'A-Za-z' '\012' < "$INPUT" |
    sort -u |
    rev |
    sort |
    rev > "$RHYME_OUT"
