---
id: 2025-12-04T07-57-57Z-dev-docker-migrations
date: 2025-12-04T07:57:57Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/docker-compose.dev.yml
  - docker/backend-entrypoint.sh
  - docker/README.md
summary: "Add backend entrypoint to auto-run migrations in dev compose"
---

## User Prompt

mysql.err.ProgrammingError) (1146, "Table 'ai_video_studio.users' doesn't exist") ... 没有自动运行迁移？

## Goals

- Ensure dev docker backend waits for DB and runs migrations automatically to avoid missing tables.

## Changes

- Added `docker/backend-entrypoint.sh`: waits for DB via SQLAlchemy, runs `python manage.py migration upgrade`, then starts uvicorn.
- Updated backend service in `docker/docker-compose.dev.yml` to use the entrypoint and mount the script.
- Documented the auto-migration behavior in `docker/README.md`.

## Validation

- Config-only change; rebuild/restart stack to apply.

## Next Steps

- `cd docker && docker compose -f docker-compose.dev.yml build ai-video-backend && docker compose -f docker-compose.dev.yml up -d ai-video-backend ai-video-nginx`.

## Linked Commits

- (pending)
