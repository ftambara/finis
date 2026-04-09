#!/usr/bin/env bash

set -euo pipefail

ROOT_CA_PATH="/data/caddy/pki/authorities/local/root.crt"
LOCAL_CERT_PATH="./caddy_root.crt"

# 1. Extract the Caddy Root CA certificate from the running Docker container
echo "Extracting Caddy Root CA certificate..."
if ! docker compose exec caddy cat "$ROOT_CA_PATH" > "$LOCAL_CERT_PATH"; then
    echo "Error: Could not extract the Caddy Root CA certificate. Make sure the 'caddy' container is running."
    exit 1
fi

# 2. Add to system trust store
echo "Adding to system trust store..."
sudo trust anchor --store "$LOCAL_CERT_PATH"
# Some systems might also need update-ca-trust
if command -v update-ca-trust >/dev/null 2>&1; then
    sudo update-ca-trust
fi

# 3. Add to Firefox's certificate database (Firefox uses its own store)
echo "Adding to Firefox profile(s)..."
FIREFOX_PATH="$HOME/.mozilla/firefox"
if [ -d "$FIREFOX_PATH" ]; then
    for profile in "$FIREFOX_PATH"/*.default*; do
        if [ -d "$profile" ]; then
            echo "Processing Firefox profile: $(basename "$profile")"
            # Add to cert9.db (Firefox version 58+)
            certutil -A -n "Caddy Local CA" -t "C,," -i "$LOCAL_CERT_PATH" -d "sql:$profile"
        fi
    done
else
    echo "No Firefox profiles found at $FIREFOX_PATH"
fi

echo "Done! Please restart Firefox and visit https://localhost."
rm "$LOCAL_CERT_PATH"
