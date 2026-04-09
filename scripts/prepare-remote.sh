#!/bin/bash
set -e

# Usage: scripts/prepare-remote.sh <server_ip> <image_tag>
IP=$1
IMAGE_TAG=$2

if [ -z "$IP" ] || [ -z "$IMAGE_TAG" ]; then
  echo "Error: Server IP address and Image Tag are required."
  echo "Usage: $0 <server_ip> <image_tag>"
  exit 1
fi

if [ -z "$PRODUCTION_ENV" ]; then
  echo "Error: PRODUCTION_ENV environment variable is not set."
  exit 1
fi

echo "Connecting to $IP to prepare deployment environment..."

# 1. Ensure directory exists and create .env
ssh "root@$IP" "mkdir -p /app/finis && cat << 'EOF' > /app/finis/.env
$PRODUCTION_ENV
IMAGE_TAG=$IMAGE_TAG
EOF"

# 2. Copy files (Image, Compose, Caddy)
echo "Copying image and config files to server..."
scp "finis_$IMAGE_TAG.tar.gz" compose.prod.yaml Caddyfile "root@$IP:/app/finis/"

# 3. Load the image
echo "Loading Docker image finis:$IMAGE_TAG..."
ssh "root@$IP" "cd /app/finis && gunzip -c finis_$IMAGE_TAG.tar.gz | docker load && rm finis_$IMAGE_TAG.tar.gz"

echo "Server preparation complete."
