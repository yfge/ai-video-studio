---
id: 2025-12-11T06-50-00Z-docker-compose-prod-stack
date: 2025-12-11T06:50:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [infra, docker, deployment]
related_paths:
  - docker/docker-compose.prod.yml
  - docker/Dockerfile.backend.prod
  - docker/Dockerfile.frontend.prod
  - docker/nginx.prod.conf
summary: "Add production-oriented Docker Compose stack and Dockerfiles for backend, frontend, and Nginx."
---

## User Prompt

- “生成生产级使用的docker-compose”
- “没有docker-compose.prod?”

## Goals

- Provide a production-ready `docker-compose.prod.yml` that builds backend and frontend images from the repo without bind mounts, exposes Nginx on port 80, and persists MySQL/Redis/uploads via named volumes.
- Add dedicated production Dockerfiles for backend and frontend builds.
- Provide a minimal Nginx production config that routes `/api` to the backend and all other paths to the Next.js frontend.

## Changes

- `docker/docker-compose.prod.yml`:
  - Defines `ai-video-mysql` (MySQL 8), `ai-video-redis` (Redis 7), `ai-video-backend`, `ai-video-frontend`, and `ai-video-nginx`.
  - Backend:
    - Builds from `docker/Dockerfile.backend.prod`, uses `env_file: .env` under `docker/`, exposes port 8000 internally, and mounts a named `uploads_data` volume for `/app/ai-pic-backend/uploads`.
  - Frontend:
    - Builds from `docker/Dockerfile.frontend.prod`, uses the same `.env`, runs `npm run start` on port 3000.
  - Nginx:
    - Uses `nginx:1.27-alpine`, mounts `docker/nginx.prod.conf` and exposes host port 80 → container 8080.
  - Persists data via named volumes `mysql_data`, `redis_data`, and `uploads_data`.
- `docker/Dockerfile.backend.prod`:
  - Based on `python:3.11-slim`, installs build deps and backend `requirements.txt`.
  - Copies `ai-pic-backend` into the image and runs `uvicorn main:app` with 4 workers on port 8000.
  - Leaves migrations/DB waiting to be handled externally or in future entrypoint improvements.
- `docker/Dockerfile.frontend.prod`:
  - Multi-stage build:
    - Builder: installs deps, copies frontend code, runs `npm run build`.
    - Runtime: copies built app, installs production dependencies (`npm ci --omit=dev`), and runs `npm run start` on port 3000.
- `docker/nginx.prod.conf`:
  - Configures upstreams for `ai-video-backend:8000` and `ai-video-frontend:3000`.
  - Routes `/api/` to backend with standard proxy headers, `_next` and `/` to frontend, listening on port 8080 (mapped to host 80 by compose).

## Validation

- Static validation only in this environment:
  - Confirmed `docker/docker-compose.prod.yml`, `docker/Dockerfile.backend.prod`, `docker/Dockerfile.frontend.prod`, and `docker/nginx.prod.conf` are syntactically valid YAML/Dockerfile/nginx configs by visual inspection and basic shell listing.
- Full runtime validation (image build + `docker compose -f docker/docker-compose.prod.yml up -d`) must be executed in a real Docker host with proper `.env` and domain/SSL settings.

## Next Steps

- Add a small section to `docker/README.md` describing how to use `docker-compose.prod.yml` (including expected `.env` keys and a sample `docker compose -f docker/docker-compose.prod.yml up -d` command).
- Optionally introduce a production backend entrypoint script that waits for MySQL and runs Alembic migrations before starting uvicorn, mirroring the dev `backend-entrypoint.sh` but without `--reload`.

## Linked Commits

- pending
