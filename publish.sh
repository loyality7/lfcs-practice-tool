#!/bin/bash

# Script to build and publish llmbuilder to PyPI

echo "Building llmbuilder package..."

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build the package
python -m build

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful!"

# Check if twine is installed
if ! command -v twine &> /dev/null
then
    echo "twine could not be found, installing..."
    pip install twine
fi

# Upload to PyPI
echo "Uploading to PyPI..."
twine upload dist/*

echo "Package published successfully!"