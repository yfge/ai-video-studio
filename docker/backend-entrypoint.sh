#!/usr/bin/env bash
set -euo pipefail

cd /app/ai-pic-backend

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[backend-entrypoint] DATABASE_URL is required" >&2
  exit 1
fi

echo "[backend-entrypoint] Waiting for database..."
python - <<'PY'
import os
import sys
import time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
engine = create_engine(url, pool_pre_ping=True)
deadline = time.time() + 60
while True:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[backend-entrypoint] Database is ready")
        sys.exit(0)
    except Exception as exc:  # pragma: no cover - runtime guard
        if time.time() > deadline:
            print(f"[backend-entrypoint] Database not ready: {exc}")
            sys.exit(1)
        time.sleep(2)
PY

echo "[backend-entrypoint] Applying migrations..."
python manage.py migration upgrade

echo "[backend-entrypoint] Starting uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
