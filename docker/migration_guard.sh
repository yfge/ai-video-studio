#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./migration_guard.sh <check|fix> [dev|prod] [--dry-run]

Examples:
  ./migration_guard.sh check dev
  ./migration_guard.sh fix prod
  ./migration_guard.sh fix dev --dry-run
EOF
}

ACTION="${1:-check}"
STACK="${2:-dev}"
DRY_RUN=0

for arg in "${@:3}"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      echo "[migration_guard] Unknown option: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$ACTION" != "check" && "$ACTION" != "fix" ]]; then
  echo "[migration_guard] Invalid action: $ACTION" >&2
  usage
  exit 1
fi

if [[ "$STACK" != "dev" && "$STACK" != "prod" ]]; then
  echo "[migration_guard] Invalid stack: $STACK (supported: dev, prod)" >&2
  usage
  exit 1
fi

COMPOSE_FILE=""
ENV_FILE=".env"
case "$STACK" in
  dev)
    COMPOSE_FILE="docker-compose.dev.yml"
    ;;
  prod)
    COMPOSE_FILE="docker-compose.prod.yml"
    ;;
esac

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[migration_guard] Missing $ENV_FILE. Run ./init_env.sh $STACK first." >&2
  exit 1
fi

COMPOSE_CMD=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

if ! "${COMPOSE_CMD[@]}" ps --status running --services | rg -xq "ai-video-backend"; then
  echo "[migration_guard] Service ai-video-backend is not running in $STACK stack." >&2
  echo "[migration_guard] Start stack first: docker compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d" >&2
  exit 1
fi

status_json=$(
  "${COMPOSE_CMD[@]}" exec -T ai-video-backend python - <<'PY'
import json
from app.core.migrations import migration_manager

print(json.dumps(migration_manager.check_migration_status()))
PY
)

status_fields=$(python - "$status_json" <<'PY'
import json
import sys

status = json.loads(sys.argv[1])
database_exists = "1" if status.get("database_exists") else "0"
needs_upgrade = "1" if status.get("needs_upgrade") else "0"
current = status.get("current_revision") or "none"
head = status.get("head_revision") or "none"
pending_count = str(status.get("pending_count", 0))
pending_list = ",".join(status.get("pending_migrations") or [])

print("|".join([database_exists, needs_upgrade, current, head, pending_count, pending_list]))
PY
)

IFS='|' read -r database_exists needs_upgrade current_revision head_revision pending_count pending_list <<< "$status_fields"

echo "[migration_guard] Stack: $STACK"
echo "[migration_guard] Current revision: $current_revision"
echo "[migration_guard] Head revision: $head_revision"
echo "[migration_guard] Pending count: $pending_count"

if [[ -n "$pending_list" ]]; then
  echo "[migration_guard] Pending revisions: $pending_list"
fi

if [[ "$database_exists" != "1" ]]; then
  echo "[migration_guard] Database connection failed." >&2
  exit 1
fi

if [[ "$ACTION" == "check" ]]; then
  if [[ "$needs_upgrade" == "1" ]]; then
    echo "[migration_guard] Migration is NOT synced. Run: ./migration_guard.sh fix $STACK" >&2
    exit 2
  fi
  echo "[migration_guard] Migration is synced."
  exit 0
fi

# ACTION=fix
if [[ "$needs_upgrade" != "1" ]]; then
  echo "[migration_guard] Already synced. No action required."
  exit 0
fi

echo "[migration_guard] Applying alembic upgrade head..."
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[migration_guard] Dry run enabled. Skip applying migrations."
  exit 0
fi

"${COMPOSE_CMD[@]}" exec -T ai-video-backend alembic upgrade head

echo "[migration_guard] Re-checking migration status..."
exec "$SCRIPT_DIR/migration_guard.sh" check "$STACK"
