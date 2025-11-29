#!/bin/bash

# Build script for local testing (does not upload to PyPI)

set -e  # Exit on error

echo "Building lfcs package locally..."
echo "================================"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info

# Build the package
echo "Building package..."
python -m build

echo ""
echo "Build successful!"
echo ""
echo "Package files created in dist/:"
ls -lh dist/
echo ""
echo "To install locally for testing:"
echo "  pip install dist/lfcs-*.whl"
echo ""
echo "To install in editable mode:"
echo "  pip install -e ."
echo ""
