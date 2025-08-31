#!/bin/bash
set -e
export DISPLAY=:0
export XAUTHORITY=$(mktemp)
xauth add $DISPLAY . $(mcookie)
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
python tests/test_system.py --verbose --output-file "test_results_$(date +%Y%m%d_%H%M%S).txt"
