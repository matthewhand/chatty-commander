#!/bin/bash

# ChattyCommander Test Runner
# This script runs the comprehensive system tests

set -e

echo "🚀 Starting ChattyCommander System Tests..."
echo "================================================"

# Ensure DISPLAY is set for GUI components
export DISPLAY=${DISPLAY:-:0}

# Ensure local repo root is on PATH so the 'chatty' dev wrapper is discoverable
export PATH="${PWD}:$PATH"

# Run the comprehensive test suite
python tests/test_system.py --verbose --output-file "test_results_$(date +%Y%m%d_%H%M%S).txt"

echo "================================================"
echo "✅ All tests completed successfully!"
echo "📊 Check the generated test report for detailed results."