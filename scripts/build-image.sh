#!/bin/bash
set -e

# Usage: scripts/build-image.sh <image_tag>
IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
  echo "Error: Image tag is required."
  exit 1
fi

echo "Building Docker image with tag finis:$IMAGE_TAG..."
docker build -t "finis:$IMAGE_TAG" .

echo "Saving image to tarball..."
docker save "finis:$IMAGE_TAG" | gzip > "finis_$IMAGE_TAG.tar.gz"

echo "Image build and save complete: finis_$IMAGE_TAG.tar.gz"
