#!/bin/bash
# Build only Ubuntu LFCS practice base image (faster for testing)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Building Ubuntu LFCS Practice Base Image"
echo "=========================================="
echo

# Build Ubuntu image
echo "Building Ubuntu 22.04 base image..."
docker build -t lfcs-practice-ubuntu:22.04 "$SCRIPT_DIR/ubuntu/"
docker tag lfcs-practice-ubuntu:22.04 lfcs-practice-ubuntu:latest
echo "✓ Ubuntu image built successfully"
echo

echo "=========================================="
echo "Ubuntu image built successfully!"
echo "=========================================="
echo
echo "Available image:"
docker images | grep lfcs-practice-ubuntu
echo
echo "To test the image, run:"
echo "  docker run --rm -it --privileged lfcs-practice-ubuntu:latest /bin/bash"
echo
echo "To use with LFCS tool:"
echo "  lfcs start"
