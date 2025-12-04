---
id: 2025-12-04T07-54-15Z-story-structure-shot-order
date: 2025-12-04T07:54:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, bugfix]
related_paths:
  - ai-pic-backend/app/schemas/story_structure.py
summary: "Fix ShotResponse forward ref for story structure schemas"
---
## User Prompt
还是有问题，继续检查直到正常为止

## Goals
- Resolve backend crash complaining `PydanticUndefinedAnnotation: ShotResponse not defined` during schema generation.

## Changes
- Moved `ShotCreate`/`ShotResponse` definitions above `SceneWithChildren` so Pydantic sees ShotResponse before it's referenced.

## Validation
- Not rerun containers here; restart backend after rebuild to confirm boot succeeds.

## Next Steps
- `cd docker && docker compose -f docker-compose.dev.yml build ai-video-backend && docker compose -f docker-compose.dev.yml up -d ai-video-backend ai-video-nginx`.

## Linked Commits
- (pending)
