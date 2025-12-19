---
id: 2025-12-19T09-38-00Z-video-task-polling
date: 2025-12-19T09:38:00Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, celery, polling, refactor]
related_paths:
  - ai-pic-backend/alembic/versions/6b747471077a_add_video_generation_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/models/__init__.py
  - ai-pic-backend/app/models/video_generation_task.py
  - ai-pic-backend/app/repositories/video_generation_task_repository.py
  - ai-pic-backend/app/services/providers/keling_provider/provider.py
  - ai-pic-backend/app/services/providers/keling_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/minimax_provider/provider.py
  - ai-pic-backend/app/services/providers/minimax_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/volcengine_provider/provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_tasks.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/video/video_task_dispatcher.py
  - ai-pic-backend/app/services/video/video_task_entrypoints.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/video/video_task_provider_resolver.py
  - ai-pic-backend/app/services/video/video_task_storyboard_updater.py
  - ai-pic-backend/app/services/video/video_task_submission_service.py
  - ai-pic-backend/app/services/video/video_task_utils.py
  - docker/docker-compose.dev.yml
  - docker/docker-compose.prod.yml
summary: "Async storyboard video submission with centralized polling and new tracking table"
---

## User Prompt
- Fix worker import issues; test via port 8089 in dev_indocker; increase image-to-video check time to 30 minutes.
- Move video generation to non-blocking submission with centralized polling (all providers), Celery beat schedule, new table, 1-hour max, and return immediately after submission.

## Goals
- Decouple storyboard video generation from synchronous polling and avoid blocking worker threads.
- Add centralized polling for all video tasks with Celery beat and a dedicated DB table.
- Enforce provider coverage and 1-hour timeout while keeping tasks non-blocking.

## Changes
- Added `video_generation_tasks` table + SQLAlchemy model/repository for tracking async video tasks.
- Introduced submission and polling services, dispatcher, and shared utilities for async video task flow.
- Implemented provider-specific async submit/status helpers for Keling, MiniMax, and Volcengine; refactored to keep function sizes within limits.
- Wired storyboard video generation to submit-only, added centralized poller task and Celery beat schedule, and added Celery beat container to docker-compose.
- Added helper modules for provider model resolution and storyboard update handling.

## Validation
- `pytest` (ai-pic-backend) timed out after 120s with existing failures (numerous failing tests before timeout).
- `./docker/build_prod_images.sh` succeeded (tag `9cacb95`).
- Chrome MCP: `http://localhost:8089/login` returned `502 Bad Gateway` (nginx), so E2E login flow could not be completed.

## Next Steps
- Restore backend availability behind nginx (502) and rerun Chrome login + storyboard video generation flow.
- Re-run full `pytest` once test environment is stable and address failing suites.

## Linked Commits
- Pending
