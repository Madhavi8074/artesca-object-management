#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
WHEELS_DIR="$BACKEND_DIR/wheels"

echo "=============================================="
echo " ARTESCA OBJECT MANAGEMENT - OFFLINE SETUP"
echo "=============================================="

echo
echo "[1/7] Checking Python..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION"

echo
echo "[2/7] Checking Node.js and npm..."

if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js is not installed."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed."
    exit 1
fi

echo "✓ Node: $(node --version)"
echo "✓ npm:  $(npm --version)"

echo
echo "[3/7] Checking PostgreSQL..."

if ! command -v psql >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL client is not installed."
    echo "Install PostgreSQL on the offline system before running this script."
    exit 1
fi

if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl is-active --quiet postgresql; then
        echo "PostgreSQL is not running. Attempting to start it..."

        if command -v sudo >/dev/null 2>&1; then
            sudo systemctl start postgresql
        else
            echo "ERROR: Cannot start PostgreSQL automatically."
            exit 1
        fi
    fi
fi

echo "✓ PostgreSQL is available"

echo
echo "[4/7] Creating Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo
echo "[5/7] Installing Python packages from LOCAL wheels..."

if [ ! -d "$WHEELS_DIR" ]; then
    echo "ERROR: $WHEELS_DIR does not exist."
    exit 1
fi

"$PIP" install \
    --no-index \
    --find-links "$WHEELS_DIR" \
    -r "$BACKEND_DIR/requirements.txt"

echo "✓ Python dependencies installed offline"

echo
echo "[6/7] Checking frontend dependencies..."

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "ERROR: frontend/node_modules does not exist."
    echo
    echo "Prepare node_modules on the internet-connected machine"
    echo "before transferring the project to the offline system."
    exit 1
fi

echo "✓ frontend/node_modules found"
echo "✓ No npm install required"

echo
echo "[7/7] Initializing database..."

cd "$BACKEND_DIR"

"$PYTHON" init_db.py

echo
echo "=============================================="
echo " OFFLINE SETUP COMPLETED"
echo "=============================================="
echo
echo "You can now run:"
echo
echo "    ./start_all.sh"
echo
