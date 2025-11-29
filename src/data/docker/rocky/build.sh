#!/bin/bash
# Build Rocky Linux base image for LFCS practice

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Rocky Linux 9 LFCS practice image..."
docker build -t lfcs-practice-rocky:9 "$SCRIPT_DIR"
docker tag lfcs-practice-rocky:9 lfcs-practice-rocky:latest

echo "✓ Rocky Linux image built successfully"
echo
echo "To test the image:"
echo "  docker run --rm -it --privileged lfcs-practice-rocky:latest /bin/bash"
