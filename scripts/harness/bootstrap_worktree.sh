#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname "$0")/../.." && pwd)
DOCKER_DIR="$ROOT_DIR/docker"
MODE="lite"
PROVIDER_MODE="${HARNESS_PROVIDER_MODE:-mock}"
NO_START=0

usage() {
  cat <<'EOF'
Usage: scripts/harness/bootstrap_worktree.sh [--mode lite] [--provider-mode mock|real] [--no-start]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --provider-mode)
      PROVIDER_MODE="$2"
      shift 2
      ;;
    --no-start)
      NO_START=1
      shift
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

RUN_ID=${HARNESS_RUN_ID:-"harness-$(date -u +%Y%m%dT%H%M%SZ)"}
WORKTREE_SLUG=$(basename "$ROOT_DIR" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')
HASH_SEED=$(python3 - <<'PY' "$ROOT_DIR"
import hashlib, sys
print(int(hashlib.sha1(sys.argv[1].encode()).hexdigest()[:6], 16))
PY
)
HARNESS_WEB_PORT=${HARNESS_WEB_PORT:-$((3100 + HASH_SEED % 200))}
HARNESS_API_PORT=${HARNESS_API_PORT:-$((8100 + HASH_SEED % 200))}
HARNESS_NGINX_PORT=${HARNESS_NGINX_PORT:-$((9100 + HASH_SEED % 200))}
PROJECT_NAME="harness-${WORKTREE_SLUG}-${HASH_SEED}"
ARTIFACT_DIR="$ROOT_DIR/artifacts/runs/$RUN_ID"
ENV_FILE="$DOCKER_DIR/.env.harness.$RUN_ID"
SOURCE_ENV="$DOCKER_DIR/.env.lite.example"
BOOTSTRAP_LOG="$ARTIFACT_DIR/bootstrap.log"

if [[ "$MODE" != "lite" ]]; then
  echo "[bootstrap_worktree] Only lite mode is isolated in the current harness foundation." >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR/screenshots"
cp "$SOURCE_ENV" "$ENV_FILE"

python3 - <<'PY' "$ENV_FILE" "$RUN_ID" "$HARNESS_WEB_PORT" "$HARNESS_API_PORT" "$HARNESS_NGINX_PORT" "$MODE" "$PROVIDER_MODE"
from pathlib import Path
import sys

env_file = Path(sys.argv[1])
run_id, web_port, api_port, nginx_port, mode, provider_mode = sys.argv[2:]
lines = env_file.read_text(encoding="utf-8").splitlines()
replacements = {
    "HARNESS_RUN_ID": run_id,
    "HARNESS_WEB_PORT": web_port,
    "HARNESS_API_PORT": api_port,
    "HARNESS_NGINX_PORT": nginx_port,
    "HARNESS_MODE": mode,
    "HARNESS_PROVIDER_MODE": provider_mode,
    "NEXT_PUBLIC_API_URL": f"http://localhost:{nginx_port}",
    "NEXT_PUBLIC_HARNESS_RUN_ID": run_id,
}
output = []
seen = set()
for line in lines:
    if "=" not in line or line.lstrip().startswith("#"):
        output.append(line)
        continue
    key, _ = line.split("=", 1)
    if key in replacements:
        output.append(f"{key}={replacements[key]}")
        seen.add(key)
    else:
        output.append(line)
for key, value in replacements.items():
    if key not in seen:
        output.append(f"{key}={value}")
env_file.write_text("\n".join(output) + "\n", encoding="utf-8")
PY

python3 - <<'PY' "$ROOT_DIR" "$RUN_ID" "$PROJECT_NAME" "$ENV_FILE" "$ARTIFACT_DIR" "$HARNESS_WEB_PORT" "$HARNESS_API_PORT" "$HARNESS_NGINX_PORT" "$MODE" "$PROVIDER_MODE" "pending"
from pathlib import Path
import json
import sys

root, run_id, project_name, env_file, artifact_dir, web_port, api_port, nginx_port, mode, provider_mode, bootstrap_status = sys.argv[1:]
manifest = {
    "run_id": run_id,
    "project_name": project_name,
    "env_file": str(Path(env_file).relative_to(root)),
    "artifact_dir": str(Path(artifact_dir).relative_to(root)),
    "bootstrap_status": bootstrap_status,
    "mode": mode,
    "provider_mode": provider_mode,
    "ports": {
        "frontend": int(web_port),
        "api": int(api_port),
        "nginx": int(nginx_port),
    },
    "urls": {
        "frontend": f"http://localhost:{web_port}",
        "api": f"http://localhost:{api_port}",
        "nginx": f"http://localhost:{nginx_port}",
    },
}
Path(artifact_dir, "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

if [[ "$NO_START" -ne 1 ]]; then
  docker compose \
    --project-name "$PROJECT_NAME" \
    --env-file "$ENV_FILE" \
    -f "$DOCKER_DIR/docker-compose.lite.yml" \
    up -d --build 2>&1 | tee "$BOOTSTRAP_LOG"
fi

python3 - <<'PY' "$ROOT_DIR" "$RUN_ID" "$PROJECT_NAME" "$ENV_FILE" "$ARTIFACT_DIR" "$HARNESS_WEB_PORT" "$HARNESS_API_PORT" "$HARNESS_NGINX_PORT" "$MODE" "$PROVIDER_MODE" "$([[ "$NO_START" -eq 1 ]] && echo 'prepared' || echo 'started')"
from pathlib import Path
import json
import sys

root, run_id, project_name, env_file, artifact_dir, web_port, api_port, nginx_port, mode, provider_mode, bootstrap_status = sys.argv[1:]
manifest = {
    "run_id": run_id,
    "project_name": project_name,
    "env_file": str(Path(env_file).relative_to(root)),
    "artifact_dir": str(Path(artifact_dir).relative_to(root)),
    "bootstrap_status": bootstrap_status,
    "mode": mode,
    "provider_mode": provider_mode,
    "ports": {
        "frontend": int(web_port),
        "api": int(api_port),
        "nginx": int(nginx_port),
    },
    "urls": {
        "frontend": f"http://localhost:{web_port}",
        "api": f"http://localhost:{api_port}",
        "nginx": f"http://localhost:{nginx_port}",
    },
}
Path(artifact_dir, "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(manifest, ensure_ascii=False))
PY
