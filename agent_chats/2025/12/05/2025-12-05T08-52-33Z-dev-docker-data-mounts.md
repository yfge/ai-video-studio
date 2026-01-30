---
id: 2025-12-05T08-52-33Z-dev-docker-data-mounts
date: 2025-12-05T08:52:33Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/docker-compose.dev.yml
summary: "Persist MySQL/Redis data under docker/ directory for dev stack"
---

## User Prompt

把docker-compose.dev.yml 的mysql 和 redis 存储映射到docker目录下

## Goals

- Store dev MySQL/Redis data under the repository’s `docker/` folder instead of named volumes.

## Changes

- Updated `docker/docker-compose.dev.yml` to mount `./mysql_data` and `./redis_data` inside the compose project for MySQL and Redis data.

## Validation

- Config-only change; rebuild/restart stack to apply.

## Next Steps

- `cd docker && docker compose -f docker-compose.dev.yml up -d` (existing containers may need `docker compose -f docker-compose.dev.yml down` first to switch from named volumes to bind mounts).

## Linked Commits

- (pending)
