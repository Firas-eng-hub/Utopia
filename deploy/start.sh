#!/usr/bin/env bash
set -euo pipefail
cd /app
: "${DATABASE_URL:?Set DATABASE_URL to the hosted PostgreSQL connection string}"
: "${SECRET_KEY:?Set a random SECRET_KEY for JWT signing}"
: "${BACKEND_CORS_ORIGINS:?Set BACKEND_CORS_ORIGINS to the exact frontend HTTPS origin}"
mkdir -p "$RESUME_UPLOAD_DIR"
if [ "$(id -u)" = 0 ]; then
    chown appuser:appuser "$RESUME_UPLOAD_DIR"
    gosu appuser python deploy/bootstrap.py
    exec gosu appuser uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
python deploy/bootstrap.py
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
