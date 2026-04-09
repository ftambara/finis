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

echo "Performing final deployment on $IP..."

ssh "root@$IP" << 'EOF'
  set -e
  cd /app/finis
  
  echo "Starting services with docker compose..."
  docker compose -f compose.prod.yaml up -d --remove-orphans
  
  echo "Reloading Caddy configuration..."
  docker compose -f compose.prod.yaml exec -T caddy caddy reload --config /etc/caddy/Caddyfile

  echo "Cleaning up old images..."
  docker image prune -f
  
  echo "Deployment successful!"
EOF
