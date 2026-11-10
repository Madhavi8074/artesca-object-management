#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID_FILE="$PROJECT_DIR/backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/frontend.pid"

echo "Stopping EasyStore services..."

if [ -f "$BACKEND_PID_FILE" ]; then
    PID=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        echo "✓ Backend stopped (PID: $PID)"
    fi
    rm -f "$BACKEND_PID_FILE"
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    PID=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        echo "✓ Frontend stopped (PID: $PID)"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# Fallback cleanup on ports 8000 and 3000
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite --port 3000" 2>/dev/null || true

echo "EasyStore services stopped."
