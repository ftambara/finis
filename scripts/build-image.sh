#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t finis:latest .

echo "Saving image to tarball..."
docker save finis:latest | gzip > finis_latest.tar.gz

echo "Image build and save complete: finis_latest.tar.gz"
