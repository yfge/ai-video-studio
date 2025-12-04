---
id: 2025-12-04T07-51-39Z-story-structure-schema-order
date: 2025-12-04T07:51:39Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, bugfix]
related_paths:
  - ai-pic-backend/app/schemas/story_structure.py
summary: "Resolve Pydantic forward ref failure for ScriptStructureResponse"
---
## User Prompt
我已经启动起来了，后端还是有问题，你用docker 检查吧

## Goals
- Fix backend startup crash caused by `PydanticUndefinedAnnotation: SceneBeatResponse not defined` when loading story structure endpoints.

## Changes
- Reordered schema definitions so `SceneBeatResponse` is declared before `SceneWithChildren` / `ScriptStructureResponse`, removing the forward-ref NameError at import time.

## Validation
- Not re-run containers here; change is minimal import-order fix. Restart backend container to pick up the update.

## Next Steps
- Rebuild/restart `ai-video-backend` image (`docker compose -f docker/docker-compose.dev.yml build ai-video-backend && docker compose -f docker/docker-compose.dev.yml up -d ai-video-backend ai-video-nginx`) to confirm service boots without the Pydantic error.

## Linked Commits
- (pending)
