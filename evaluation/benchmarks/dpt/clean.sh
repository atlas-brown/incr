#!/bin/bash
cd "$(dirname "$0")" || exit 1

rm -rf inputs/dpt.min/dpt inputs/dpt.small inputs/dpt.full
rm -rf cache
rm -rf outputs