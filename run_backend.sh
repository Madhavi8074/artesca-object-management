#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/backend"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Starting EasyStore Backend (FastAPI) on http://127.0.0.1:8000..."
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
