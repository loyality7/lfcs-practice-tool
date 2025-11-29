#!/bin/bash
# Build CentOS base image for LFCS practice

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building CentOS Stream 9 LFCS practice image..."
docker build -t lfcs-practice-centos:stream9 "$SCRIPT_DIR"
docker tag lfcs-practice-centos:stream9 lfcs-practice-centos:latest

echo "✓ CentOS image built successfully"
echo
echo "To test the image:"
echo "  docker run --rm -it --privileged lfcs-practice-centos:latest /bin/bash"
