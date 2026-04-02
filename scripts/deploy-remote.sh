#!/bin/bash
set -e

# Usage: scripts/deploy-remote.sh <server_ip> <image_tag>
IP=$1
IMAGE_TAG=$2

if [ -z "$IP" ] || [ -z "$IMAGE_TAG" ]; then
  echo "Error: Server IP address and Image Tag are required."
  echo "Usage: $0 <server_ip> <image_tag>"
  exit 1
fi

echo "Connecting to $IP to ensure deployment directory exists..."
ssh "root@$IP" "mkdir -p /app/finis"

echo "Creating production .env file on server..."
# Pass individual env vars or the whole file content
ssh "root@$IP" "cat << 'EOF' > /app/finis/.env
$PRODUCTION_ENV
IMAGE_TAG=$IMAGE_TAG
EOF"

echo "Copying image and config files to server..."
scp "finis_$IMAGE_TAG.tar.gz" compose.prod.yaml Caddyfile "root@$IP:/app/finis/"

echo "Loading image and restarting services on server..."
ssh "root@$IP" << 'EOF'
  set -e
  cd /app/finis
  
  # Load the image tag from the .env we just created
  source .env

  echo "Loading Docker image finis:$IMAGE_TAG (this may take a minute)..."
  gunzip -c finis_$IMAGE_TAG.tar.gz | docker load
  
  echo "Starting services with docker compose..."
  docker compose -f compose.prod.yaml up -d
  
  echo "Cleaning up..."
  rm finis_$IMAGE_TAG.tar.gz
  
  echo "Deployment successful!"
EOF
