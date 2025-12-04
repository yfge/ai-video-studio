#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo "[dev_in_docker] Missing .env; copy docker/.env.example and set required keys." >&2
  exit 1
fi

echo "[dev_in_docker] Building dev images..."
docker compose -f docker-compose.dev.yml build

echo "[dev_in_docker] Starting stack (Ctrl+C to stop)..."
docker compose -f docker-compose.dev.yml up
