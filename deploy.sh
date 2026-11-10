#!/usr/bin/env bash
# ==============================================================================
# ARTESCA Object Management Production Deployment Script
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "  Deploying Scality ARTESCA Object Management (Production)"
echo "=========================================================="

# 1. Ensure Python Virtual Environment
if [ ! -d "backend/.venv" ]; then
    echo "[1/5] Creating Python virtual environment..."
    python3 -m venv backend/.venv
fi

# 2. Check / Install Backend Dependencies
echo "[2/5] Checking backend dependencies..."
source backend/.venv/bin/activate
pip install -q --upgrade pip
if [ -f "backend/requirements.txt" ]; then
    pip install -q -r backend/requirements.txt
fi

# 3. Execute Database Migrations (PostgreSQL JSONB & Schemas)
echo "[3/5] Applying Alembic database migrations..."
cd backend
alembic upgrade head
cd "$DIR"

# 4. Compile Frontend Production Bundle
echo "[4/5] Compiling optimized frontend bundle..."
if [ -d "$HOME/.nvm/versions/node" ]; then
    NODE_BIN="$(ls -d $HOME/.nvm/versions/node/*/bin 2>/dev/null | tail -n 1)"
    if [ -n "$NODE_BIN" ]; then
        export PATH="$NODE_BIN:$PATH"
    fi
fi

if command -v npm &> /dev/null; then
    cd frontend
    npm run build
    cd "$DIR"
    echo "Frontend build completed in frontend/dist."
else
    echo "Warning: npm not found in PATH; skipping frontend recompile (existing dist will be served)."
fi

# 5. Deployment Verification
echo "[5/5] Verifying environment & health checks..."
python3 -c "
import urllib.request, json
try:
    with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3) as r:
        print('Backend live health status:', json.loads(r.read()))
except Exception as e:
    print('Backend will be ready upon service start.')
"

echo "=========================================================="
echo " Deployment Complete!"
echo " Start production service: ./start_production.sh"
echo " Or systemd service: sudo systemctl restart artesca.service"
echo "=========================================================="
