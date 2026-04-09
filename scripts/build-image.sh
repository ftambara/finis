#!/bin/bash
set -e

# Usage: scripts/build-image.sh <image_tag>
IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
  echo "Error: Image tag is required."
  exit 1
fi

echo "Building Docker image with tag finis:$IMAGE_TAG..."
docker buildx build \
  --cache-from type=gha \
  --cache-to type=gha,mode=max \
  --tag "finis:$IMAGE_TAG" \
  --output type=docker,dest=finis_$IMAGE_TAG.tar \
  .

echo "Compressing image..."
gzip -f "finis_$IMAGE_TAG.tar"

echo "Image build and save complete: finis_$IMAGE_TAG.tar.gz"
