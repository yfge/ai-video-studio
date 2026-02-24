#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

ENV_FILE=".env.lite"
COMPOSE_FILE="docker-compose.lite.yml"

if [ ! -f "$ENV_FILE" ]; then
  echo "[dev_lite_in_docker] Missing $ENV_FILE; run ./init_env.sh lite first." >&2
  exit 1
fi

echo "[dev_lite_in_docker] Building lite images..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build

echo "[dev_lite_in_docker] Starting lite stack (Ctrl+C to stop)..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up
