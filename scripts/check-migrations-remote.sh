#!/bin/bash
set -e

# Usage: scripts/check-migrations-remote.sh <server_ip> <image_tag>
IP=$1
IMAGE_TAG=$2

if [ -z "$IP" ] || [ -z "$IMAGE_TAG" ]; then
  echo "Error: Server IP address and Image Tag are required."
  echo "Usage: $0 <server_ip> <image_tag>"
  exit 1
fi

echo "Checking for pending migrations on $IP using image finis:$IMAGE_TAG..."

# We run the migration check using the new image against the production database
# If it exits with 0, no migrations are pending.
# If it exits with non-zero, migrations are pending.
ssh "root@$IP" "cd /app/finis && IMAGE_TAG=$IMAGE_TAG docker compose -f compose.prod.yaml run --rm app python manage.py migrate --check"

echo "No pending migrations detected."
