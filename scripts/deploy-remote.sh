#!/bin/bash
set -e

# Usage: scripts/deploy-remote.sh <server_ip>
IP=$1

if [ -z "$IP" ]; then
  echo "Error: Server IP address is required."
  echo "Usage: $0 <server_ip>"
  exit 1
fi

echo "Connecting to $IP to ensure deployment directory exists..."
ssh root@$IP "mkdir -p /app/finis"

echo "Creating production .env file on server..."
# Pass individual env vars or the whole file content
ssh root@$IP "cat << 'EOF' > /app/finis/.env
$PRODUCTION_ENV
EOF"

echo "Copying image and config files to server..."
scp finis_latest.tar.gz compose.prod.yaml Caddyfile root@$IP:/app/finis/

echo "Loading image and restarting services on server..."
ssh root@$IP << 'EOF'
  set -e
  cd /app/finis
  
  echo "Loading Docker image (this may take a minute)..."
  gunzip -c finis_latest.tar.gz | docker load
  
  echo "Starting services with docker compose..."
  docker compose -f compose.prod.yaml up -d
  
  echo "Cleaning up..."
  rm finis_latest.tar.gz
  
  echo "Deployment successful!"
EOF
