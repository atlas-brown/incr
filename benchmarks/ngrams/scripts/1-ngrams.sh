#!/bin/bash

# Combine terms to create n-grams (for n=1,2,3)
# Usage: ./combine.sh < terms > n-grams

mkfifo p1

tee >(tee p1 | sed '/\t$/d') 

rm p1
