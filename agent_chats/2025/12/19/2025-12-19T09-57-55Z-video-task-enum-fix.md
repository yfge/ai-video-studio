---
id: 2025-12-19T09-57-55Z-video-task-enum-fix
date: 2025-12-19T09:57:55Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, video, bugfix]
related_paths:
  - ai-pic-backend/app/models/video_generation_task.py
summary: "Align video_generation_tasks enum mapping with lowercase DB values"
---

## User Prompt
- Celery poller crashed: `LookupError: 'submitted' is not among the defined enum values`.

## Goals
- Ensure SQLAlchemy enum mapping matches lowercase values in the database enum.

## Changes
- Updated `VideoGenerationTask.status` to use the DB enum name and map enum values (`pending/submitted/...`) via `values_callable`.

## Validation
- `pytest` (ai-pic-backend) timed out after 120s with existing failures.
- `./docker/build_prod_images.sh` succeeded (tag `01cbcd1`).
- Chrome MCP: verified storyboard page loads at `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard`.

## Next Steps
- Re-run the video polling task once the worker is restarted to confirm the enum lookup error is resolved.

## Linked Commits
- Pending
