---
id: 2025-12-19T12-29-09Z-dialogue-audio-sort-fix
date: 2025-12-19T12:29:09Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, audio]
related_paths:
  - ai-pic-backend/app/services/voice_binding_service.py
summary: "Reduce sort memory usage when resolving latest scripts for dialogue audio"
---

## User Prompt

生成对白音轨失败，MySQL 报 out of sort memory，需要修复。

## Goals

- Avoid large ORDER BY sorts when selecting latest scripts per episode.

## Changes

- Replaced ORDER BY + Python de-dup with a grouped subquery (max script id per episode) in `_count_story_episodes_with_character`.

## Validation

- `pytest` (ai-pic-backend): timed out after 120s; multiple pre-existing failures surfaced during run.
- `./docker/build_prod_images.sh` succeeded.
- Chrome MCP: `http://localhost:8089/stories` loaded (empty state); no further E2E API validation due to backend API failures in prior run.

## Next Steps

- Re-run targeted tests for dialogue audio when backend services are healthy.

## Linked Commits

- (pending)
