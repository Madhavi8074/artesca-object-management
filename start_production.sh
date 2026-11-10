#!/usr/bin/env bash
# ==============================================================================
# Start EasyStore Production Multi-Worker Server
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/backend"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Load environment configuration if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"

echo "=========================================================="
echo " Starting EasyStore Production Server"
echo " Host: $HOST, Port: $PORT, Workers: $WORKERS"
echo " Interactive Docs: http://$HOST:$PORT/docs"
echo "=========================================================="

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
