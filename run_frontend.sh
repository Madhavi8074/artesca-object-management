#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/frontend"

# Ensure node/npm are in PATH if installed via NVM
if [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_BIN="$(ls -d $HOME/.nvm/versions/node/*/bin 2>/dev/null | tail -n 1)"
    if [ -n "$NODE_BIN" ]; then
        export PATH="$NODE_BIN:$PATH"
    fi
fi

echo "Starting EasyStore Frontend (Vite) on http://localhost:3000..."
exec npm run dev -- --port 3000 --host
