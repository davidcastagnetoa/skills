#!/usr/bin/env bash
set -euo pipefail

echo "=== VerifID Development Setup ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3.12+ is required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }

# Create .env from example if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[OK] Created .env from .env.example"
else
    echo "[OK] .env already exists"
fi

# Create virtual environment
if [ ! -d backend/.venv ]; then
    python3 -m venv backend/.venv
    echo "[OK] Created virtual environment"
else
    echo "[OK] Virtual environment already exists"
fi

# Install dependencies
echo "[..] Installing Python dependencies..."
backend/.venv/bin/pip install -q --upgrade pip
backend/.venv/bin/pip install -q -e "backend[dev]"
echo "[OK] Dependencies installed"

# Create models directory
mkdir -p models
echo "[OK] Models directory ready"

# Start infrastructure
echo "[..] Starting Docker services..."
make up
echo "[OK] Docker services started"

# Wait for services
echo "[..] Waiting for PostgreSQL..."
sleep 3

# Run migrations
echo "[..] Running database migrations..."
make migrate
echo "[OK] Migrations complete"

echo ""
echo "=== Setup Complete ==="
echo "  API:        http://localhost:8000"
echo "  Docs:       http://localhost:8000/docs"
echo "  MinIO:      http://localhost:9001"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
