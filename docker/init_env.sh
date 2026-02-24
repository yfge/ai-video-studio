#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./init_env.sh <dev|prod|lite> [--force] [--dry-run]

Examples:
  ./init_env.sh dev
  ./init_env.sh prod --force
  ./init_env.sh lite --dry-run
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

MODE="$1"
shift

FORCE=0
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      FORCE=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      echo "[init_env] Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

SOURCE_FILE=""
TARGET_FILE=""
case "$MODE" in
  dev)
    SOURCE_FILE=".env.example"
    TARGET_FILE=".env"
    ;;
  prod)
    SOURCE_FILE=".env.prod.example"
    TARGET_FILE=".env"
    ;;
  lite)
    SOURCE_FILE=".env.lite.example"
    TARGET_FILE=".env.lite"
    ;;
  *)
    echo "[init_env] Invalid mode: $MODE" >&2
    usage
    exit 1
    ;;
esac

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "[init_env] Missing source template: $SOURCE_FILE" >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[init_env] Dry run: $SOURCE_FILE -> $TARGET_FILE"
  exit 0
fi

if [[ -f "$TARGET_FILE" && "$FORCE" -ne 1 ]]; then
  echo "[init_env] $TARGET_FILE already exists. Use --force to overwrite." >&2
  exit 1
fi

cp "$SOURCE_FILE" "$TARGET_FILE"
echo "[init_env] Wrote $TARGET_FILE from $SOURCE_FILE"
