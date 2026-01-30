---
id: 2025-12-04T07-37-00Z-dev-docker-nginx
date: 2025-12-04T07:37:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/docker-compose.dev.yml
  - docker/nginx.dev.conf
  - docker/.env.example
  - docker/README.md
summary: "Add nginx frontend for dev stack and reduce exposed ports"
---

## User Prompt

加上nginx 不要暴漏太多端口不方便管理

## Goals

- Introduce nginx to front the dev stack and provide a single external entrypoint.
- Trim exposed ports to keep services internal where possible.

## Changes

- Added `docker/nginx.dev.conf` proxying `/api` to backend and everything else to frontend.
- Updated `docker-compose.dev.yml` to include nginx (port 8080 only), removed frontend/redis host ports, kept backend/mysql internal.
- Adjusted `.env.example` and `docker/README.md` to use the nginx entrypoint (`host.docker.internal:8080` by default) and document the new topology.

## Validation

- Config-only change; Docker daemon unavailable in this environment, so compose stack not executed here.

## Next Steps

- On a Docker-capable host: `cd docker && ./dev_in_docker.sh`, then access `http://localhost:8080`.
- If `host.docker.internal` is unavailable (Linux), set `NEXT_PUBLIC_API_URL=http://localhost:8080` in `.env`.

## Linked Commits

- (pending)
