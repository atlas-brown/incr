#!/bin/bash

# Combine terms to create n-grams (for n=1,2,3)
# Usage: ./combine.sh < terms > n-grams

mkfifo p1 p2

tee >(tee p1 | tail +2 | paste <(cat p1) - | sed '/\t$/d') >(tee p2 | tail +2 | paste <(cat p2) -) 

rm p1 p2
