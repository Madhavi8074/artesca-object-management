#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

BACKEND_LOG="$PROJECT_DIR/backend.log"
FRONTEND_LOG="$PROJECT_DIR/frontend.log"

echo "=============================================="
echo " EASYSTORE OBJECT MANAGEMENT SYSTEM"
echo "=============================================="

# ------------------------------------------------
# 1. Check Python environment
# ------------------------------------------------
echo
echo "[1/3] Checking backend environment..."

if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Creating virtual environment and installing backend requirements..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

# ------------------------------------------------
# 2. Start FastAPI
# ------------------------------------------------
echo
echo "[2/3] Starting FastAPI backend on http://127.0.0.1:8000..."

cd "$BACKEND_DIR"

nohup "$VENV_DIR/bin/python" -m uvicorn \
    app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    > "$BACKEND_LOG" 2>&1 &

BACKEND_PID=$!
echo "$BACKEND_PID" > "$PROJECT_DIR/backend.pid"

sleep 2

if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "✓ Backend started (PID: $BACKEND_PID)"
else
    echo "ERROR: Backend failed to start. Check $BACKEND_LOG"
    exit 1
fi

# ------------------------------------------------
# 3. Start Frontend
# ------------------------------------------------
echo
echo "[3/3] Starting frontend on http://localhost:3000..."

cd "$FRONTEND_DIR"

if [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_BIN="$(ls -d $HOME/.nvm/versions/node/*/bin 2>/dev/null | tail -n 1)"
    if [ -n "$NODE_BIN" ]; then
        export PATH="$NODE_BIN:$PATH"
    fi
fi

nohup npm run dev -- --port 3000 --host 127.0.0.1 \
    > "$FRONTEND_LOG" 2>&1 &

FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PROJECT_DIR/frontend.pid"

sleep 2

if kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "✓ Frontend started (PID: $FRONTEND_PID)"
else
    echo "ERROR: Frontend failed to start. Check $FRONTEND_LOG"
    exit 1
fi

echo
echo "=============================================="
echo " EASYSTORE SYSTEM STARTED SUCCESSFULLY"
echo "=============================================="
echo
echo "Frontend:          http://localhost:3000"
echo "Backend API:       http://localhost:8000"
echo "Interactive Docs:  http://localhost:8000/docs"
echo "Health Check:      http://localhost:8000/health"
echo
echo "To stop:           ./stop_all.sh"
echo "=============================================="
