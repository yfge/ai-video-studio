---
id: 2025-12-04T08-03-28Z-dev-docker-migration-noninteractive
date: 2025-12-04T08:03:28Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/backend-entrypoint.sh
summary: "Make dev backend migrations non-interactive and skip mysqldump"
---

## User Prompt

backend-entrypoint shows mysqldump missing and prompt "确认升级数据库吗？"

## Goals

- Prevent dev container from blocking on interactive migration confirmation.
- Avoid mysqldump dependency in dev by skipping backups.

## Changes

- Updated `docker/backend-entrypoint.sh` to run `yes | python manage.py migration upgrade --no-backup`, removing prompts and backup requirements.

## Validation

- Config-only change; rebuild/restart backend container to apply.

## Next Steps

- `cd docker && docker compose -f docker-compose.dev.yml build ai-video-backend && docker compose -f docker-compose.dev.yml up -d ai-video-backend ai-video-nginx` then check logs.

## Linked Commits

- (pending)
