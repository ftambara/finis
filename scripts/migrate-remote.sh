#!/bin/bash
set -e

# Usage: scripts/migrate-remote.sh <server_ip> <image_tag>
IP=$1
IMAGE_TAG=$2

if [ -z "$IP" ] || [ -z "$IMAGE_TAG" ]; then
  echo "Error: Server IP address and Image Tag are required."
  echo "Usage: $0 <server_ip> <image_tag>"
  exit 1
fi

echo "Applying migrations on $IP using image finis:$IMAGE_TAG..."

# Run the migration using the new image against the production database
ssh "root@$IP" "cd /app/finis && IMAGE_TAG=$IMAGE_TAG docker compose -f compose.prod.yaml run --rm app python manage.py migrate"

echo "Migrations applied successfully."
