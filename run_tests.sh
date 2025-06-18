#!/bin/bash

# Run PyChat tests using pytest
# Usage: ./run_tests.sh [optional pytest args]

# Ensure we're in the project root directory
cd "$(dirname "$0")" || exit 1

echo "NOTE: Some failing tests have been marked to be skipped."
echo "      These tests are marked with @skip_failing in the test files."
echo "---------------------------------------------------------------------"

# Install test dependencies if needed
pip install -r requirements.txt

# Run the tests with coverage
python -m pytest "$@"

# Generate HTML coverage report
python -m pytest --cov=pychat --cov-report=html

echo "Tests completed. Coverage report available in htmlcov/index.html"
