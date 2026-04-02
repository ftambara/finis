#!/bin/bash
# scripts/setup-ssh.sh
# 
# Purpose: Prepares the CI/CD environment for SSH-based deployment.
# It configures the private key and handles host key verification 
# to ensure non-interactive, secure connections to the remote server.
#
# Requirements:
# - SSH_PRIVATE_KEY: Environment variable containing the private key.
# - SERVER_IP: The target server IP address.

set -euo pipefail

if [[ -z "${SSH_PRIVATE_KEY:-}" ]]; then
  echo "Error: SSH_PRIVATE_KEY environment variable is not set."
  exit 1
fi

if [[ -z "${SERVER_IP:-}" ]]; then
  echo "Error: SERVER_IP environment variable is not set."
  exit 1
fi

# 1. Create the .ssh directory with restricted permissions.
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 2. Write the private key to a file. 
echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519

# 3. Use ssh-keyscan to retrieve the server's public host key.
# This prevents the "The authenticity of host ... can't be established" 
# interactive prompt that would hang the CI pipeline.
echo "Retrieving public host key for $SERVER_IP..."
ssh-keyscan -H "$SERVER_IP" >> ~/.ssh/known_hosts

echo "SSH environment successfully configured for $SERVER_IP."
