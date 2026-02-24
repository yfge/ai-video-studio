#!/usr/bin/env bash
set -euo pipefail

cd /app/ai-pic-backend

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[backend-entrypoint] DATABASE_URL is required" >&2
  exit 1
fi

is_sqlite=0
if [[ "${DATABASE_URL}" == sqlite* ]]; then
  is_sqlite=1
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

echo "[backend-entrypoint] Applying migrations via alembic upgrade head..."
if ! alembic upgrade head; then
  if [[ "$is_sqlite" == "1" && "${SQLITE_MIGRATION_FALLBACK_CREATE_ALL:-1}" == "1" ]]; then
    echo "[backend-entrypoint] Alembic migration failed on SQLite; reset DB and fallback to create_all"
    python - <<'PY'
from pathlib import Path

from app.core.database import Base, engine
import app.models  # noqa: F401 - ensure models are registered on metadata

if engine.url.get_backend_name() == "sqlite":
    db_path = engine.url.database
    if db_path and db_path != ":memory:":
        db_file = Path(db_path)
        if db_file.exists():
            db_file.unlink()
        db_file.parent.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)
print("[backend-entrypoint] SQLite schema initialized via create_all")
PY
  else
    echo "[backend-entrypoint] Migration failed" >&2
    exit 1
  fi
fi

echo "[backend-entrypoint] Starting uvicorn..."
if [[ "${UVICORN_RELOAD:-1}" == "1" ]]; then
  echo "[backend-entrypoint] Using reload mode for development"
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
  workers="${UVICORN_WORKERS:-4}"
  echo "[backend-entrypoint] Using ${workers} workers for production"
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers "${workers}"
fi
