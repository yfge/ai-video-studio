---
id: 2025-12-04T08-05-44Z-dev-docker-alembic
date: 2025-12-04T08:05:44Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/backend-entrypoint.sh
summary: "Switch dev backend entrypoint to alembic upgrade head"
---

## User Prompt

Migrations still prompt even after non-interactive tweaks; need to ensure auto migration succeeds.

## Goals

- Avoid click prompts entirely and skip mysqldump by running alembic directly in dev.

## Changes

- Updated `docker/backend-entrypoint.sh` to call `alembic upgrade head` after DB readiness, instead of piping to `manage.py`.

## Validation

- Config-only change; rebuild/restart dev backend to apply.

## Next Steps

- `cd docker && docker compose -f docker-compose.dev.yml build ai-video-backend && docker compose -f docker-compose.dev.yml up -d ai-video-backend ai-video-nginx`, then check logs for successful migration.

## Linked Commits

- (pending)
