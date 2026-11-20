#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

echo "Installing backend dependencies..."
.venv/bin/python -m pip install -q -r backend/requirements.txt

if [ ! -f "frontend/dist/index.html" ]; then
  echo "Building frontend..."
  (cd frontend && npm install && npm run build)
fi

if [ ! -f "backend/.env" ]; then
  echo "WARNING: backend/.env not found. Copy backend/.env.example to backend/.env and set DEEPSEEK_API_KEY for AI features." >&2
fi

echo ""
echo "ReelCrate: http://127.0.0.1:8000"
echo ""
exec .venv/bin/python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
