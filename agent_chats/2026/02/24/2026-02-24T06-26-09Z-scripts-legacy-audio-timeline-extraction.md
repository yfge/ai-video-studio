---
id: 2026-02-24T06-26-09Z-scripts-legacy-audio-timeline-extraction
date: 2026-02-24T06:26:09Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, api, scripts, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/integration/test_duration_control_api.py
  - tasks.md
summary: "[refactor] Migrate dialogue/timeline routes out of scripts_legacy and wire task worker imports to scripts package"
---

## User Prompt

继续

## Goals

- Continue the P0 `scripts_legacy.py` migration by extracting dialogue audio/timeline pipeline routes.
- Keep existing API behavior and Celery task entrypoints stable.
- Reduce legacy file size and update task board progress.

## Changes

- Added new script endpoint modules:
  - `ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py`
- Updated `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py` to:
  - export new task processors,
  - mount new routers on the package router.
- Removed migrated route/task-processor code from `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py` and cleaned now-unused imports.
- Updated `ai-pic-backend/app/services/task_worker.py` so `timeline_pipeline_generate_task` imports `_process_timeline_pipeline_task` from `app.api.v1.endpoints.scripts` instead of `scripts_legacy`.
- Updated integration tests in `ai-pic-backend/tests/integration/test_duration_control_api.py` to monkeypatch new module locations.
- Updated `tasks.md` progress text for legacy split status and current line count.

## Validation

- Static checks:
  - `cd ai-pic-backend && ruff check app/api/v1/endpoints/scripts/__init__.py app/api/v1/endpoints/scripts/audio_pipeline_utils.py app/api/v1/endpoints/scripts/audio_timeline.py app/api/v1/endpoints/scripts/dialogue_audio.py app/api/v1/endpoints/scripts/timeline_pipeline.py app/api/v1/endpoints/scripts_legacy.py app/services/task_worker.py tests/integration/test_duration_control_api.py`
- Tests:
  - `cd ai-pic-backend && pytest tests/integration/test_duration_control_api.py`
  - `cd ai-pic-backend && pytest`
- Pre-commit gate:
  - `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/services/task_worker.py ai-pic-backend/tests/integration/test_duration_control_api.py tasks.md`
- Production image build:
  - `./docker/build_prod_images.sh` (backend + frontend buildx/push succeeded)
- Chrome MCP E2E (lite stack on `http://localhost:8089`):
  - Logged in with `geyunfei / Gyf@845261`.
  - Called:
    - `POST /api/v1/scripts/1/dialogue-audio/generate-async` → 200, task created.
    - `POST /api/v1/scripts/1/audio-timeline/generate-async` → 200, task created.
    - `POST /api/v1/scripts/1/timeline-pipeline/generate-async` → 200, task created.
  - Verified `/tasks` page shows corresponding task types.
  - Observed lite-mode runtime issue: created tasks failed with `Already running asyncio in this thread` (recorded as existing risk surfaced during validation; route extraction itself remained reachable and task creation succeeded).

## Next Steps

- Migrate remaining `storyboard/from-audio-timeline` route out of `scripts_legacy.py`.
- Address lite-mode async execution conflict (`anyio.run` under already-running loop) for audio/timeline processors.

## Linked Commits

- pending (this entry is committed together with the refactor changes)
