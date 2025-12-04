---
id: 2025-12-04T07-42-49Z-dev-docker-ports
date: 2025-12-04T07:42:49Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [devops, docker]
related_paths:
  - docker/docker-compose.dev.yml
  - docker/README.md
summary: "Limit dev stack exposure to nginx only"
---
## User Prompt
除了nginx 以外 ，其他的端口都不要暴露

## Goals
- Keep only nginx exposed; make MySQL internal-only in the dev compose stack.
- Reflect the change in developer docs.

## Changes
- Removed MySQL host port mapping from `docker/docker-compose.dev.yml`.
- Updated `docker/README.md` to note MySQL is internal-only and suggest using `docker exec` for access.

## Validation
- Config-only change; Docker not run in this environment.

## Next Steps
- If host access to MySQL is needed temporarily, add a one-off port mapping locally or use `docker exec -it ai-video-mysql mysql -uroot -pai-video`.

## Linked Commits
- (pending)
