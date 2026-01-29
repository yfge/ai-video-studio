---
id: 2026-01-29T15-17-53Z-backend-video-provider-task-id-len
date: 2026-01-29T15:17:53Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, db, migration, video]
related_paths:
  - ai-pic-backend/alembic/versions/a97c737e5d56_ensure_video_provider_task_id_len_512.py
  - ai-pic-backend/tests/unit/models/test_video_generation_task_model.py
  - tasks.md
summary: "Add defensive Alembic migration and regression test to ensure video provider_task_id supports Vertex operation names."
---

## User Prompt

- 选择任务：1（继续 P0-2：provider_task_id 长度回归 + 迁移链路）

## Goals

- Prevent MySQL 1406 errors when provider task IDs exceed historical limits (e.g. Vertex operation names).
- Ensure new installs/upgrades consistently end up with a safe column length.
- Add a regression test to avoid accidental shrinking.

## Changes

- Added Alembic migration `a97c737e5d56_ensure_video_provider_task_id_len_512.py`:
  - Inspects current schema and ensures `video_generation_tasks.provider_task_id` is at least `VARCHAR(512)`.
- Added unit test `ai-pic-backend/tests/unit/models/test_video_generation_task_model.py` asserting the SQLAlchemy model uses `String(512+)`.
- Updated `tasks.md` to mark the provider_task_id length fix complete.

## Validation

- Docker (local dev stack):
  - `alembic upgrade head` applied migration `f621ea056717 -> a97c737e5d56`
  - Verified via DB query inside container: `provider_task_id_length == 512`
- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome MCP DevTools: still unavailable (`Transport closed`).

## Next Steps

- Continue P0-2: unify/standardize generation metadata persisted to DB (`provider/model/task_id/width/height/duration/mime/sha256`).

## Linked Commits

- (pending)

