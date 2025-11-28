#!/bin/bash
# Build all LFCS practice base images

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Building LFCS Practice Base Images"
echo "=========================================="
echo

# Build Ubuntu image
echo "Building Ubuntu 22.04 base image..."
docker build -t lfcs-practice-ubuntu:22.04 "$SCRIPT_DIR/ubuntu/"
docker tag lfcs-practice-ubuntu:22.04 lfcs-practice-ubuntu:latest
echo "✓ Ubuntu image built successfully"
echo

# Build CentOS image
echo "Building CentOS Stream 9 base image..."
docker build -t lfcs-practice-centos:stream9 "$SCRIPT_DIR/centos/"
docker tag lfcs-practice-centos:stream9 lfcs-practice-centos:latest
echo "✓ CentOS image built successfully"
echo

# Build Rocky Linux image
echo "Building Rocky Linux 9 base image..."
docker build -t lfcs-practice-rocky:9 "$SCRIPT_DIR/rocky/"
docker tag lfcs-practice-rocky:9 lfcs-practice-rocky:latest
echo "✓ Rocky Linux image built successfully"
echo

echo "=========================================="
echo "All images built successfully!"
echo "=========================================="
echo
echo "Available images:"
docker images | grep lfcs-practice
echo
echo "To test an image, run:"
echo "  docker run --rm -it --privileged lfcs-practice-ubuntu:latest /bin/bash"
