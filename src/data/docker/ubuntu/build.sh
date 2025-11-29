#!/bin/bash
# Build Ubuntu base image for LFCS practice

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Ubuntu 22.04 LFCS practice image..."
docker build -t lfcs-practice-ubuntu:22.04 "$SCRIPT_DIR"
docker tag lfcs-practice-ubuntu:22.04 lfcs-practice-ubuntu:latest

echo "✓ Ubuntu image built successfully"
echo
echo "To test the image:"
echo "  docker run --rm -it --privileged lfcs-practice-ubuntu:latest /bin/bash"
