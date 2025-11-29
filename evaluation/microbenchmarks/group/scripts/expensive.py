#!/bin/python3

import sys
import tensorflow
import segment_anything
import torch
import torchvision

if not sys.stdin.isatty():
    for line in sys.stdin.buffer:
        sys.stdout.buffer.write(line)
    sys.stdout.buffer.flush()