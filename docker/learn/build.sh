#!/bin/bash
# Build the LFCS learning environment Docker image

set -e

IMAGE_NAME="lfcs-learn-ubuntu"
TAG="latest"

echo "Building LFCS learning environment image..."
docker build -t "${IMAGE_NAME}:${TAG}" .

echo ""
echo "✓ Image built successfully: ${IMAGE_NAME}:${TAG}"
echo ""
echo "To use this image, update your config to use: ${IMAGE_NAME}:${TAG}"
