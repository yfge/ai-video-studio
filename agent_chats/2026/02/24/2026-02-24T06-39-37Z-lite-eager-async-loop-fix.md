---
id: 2026-02-24T06-39-37Z-lite-eager-async-loop-fix
date: 2026-02-24T06:39:37Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, lite, async, fix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/tests/unit/test_scripts_audio_pipeline_utils.py
  - tasks.md
summary: "Fix lite eager execution loop conflict for scripts dialogue/timeline async processors"
---

## User Prompt

继续

## Goals

- Continue implementation with the next actionable backend improvement.
- Fix lite mode eager-task runtime error `Already running asyncio in this thread` for migrated scripts audio/timeline processors.
- Add automated coverage for the new async runner behavior.

## Changes

- Added `run_async_task_sync` to `ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py`:
  - Runs coroutine via `anyio.run` in normal worker context.
  - Detects existing running loop and offloads coroutine execution to a dedicated thread in eager/request context.
- Updated processor modules to use shared runner instead of direct `anyio.run(...)`:
  - `ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py`
- Added unit tests for runner behavior:
  - `ai-pic-backend/tests/unit/test_scripts_audio_pipeline_utils.py`
  - covers no-loop execution, running-loop thread offload, and exception propagation.
- Updated task board note in `tasks.md` to record the lite eager async-loop fix progress.

## Validation

- Targeted lint:
  - `cd ai-pic-backend && ruff check app/api/v1/endpoints/scripts/audio_pipeline_utils.py app/api/v1/endpoints/scripts/dialogue_audio.py app/api/v1/endpoints/scripts/audio_timeline.py app/api/v1/endpoints/scripts/timeline_pipeline.py tests/unit/test_scripts_audio_pipeline_utils.py`
- Targeted tests:
  - `cd ai-pic-backend && pytest tests/unit/test_scripts_audio_pipeline_utils.py`
  - `cd ai-pic-backend && pytest tests/integration/test_duration_control_api.py`
- Full backend tests:
  - `cd ai-pic-backend && pytest` (1886 passed, 87 skipped)
- Production image build gate:
  - `./docker/build_prod_images.sh` (backend/frontend buildx + push succeeded)
- Chrome MCP E2E (lite stack):
  - Opened `http://localhost:8089`, authenticated as `geyunfei`.
  - Triggered `POST /api/v1/scripts/1/dialogue-audio/generate-async` and verified task status `completed` with description `对白音轨生成完成`.
  - Triggered `POST /api/v1/scripts/1/audio-timeline/generate-async` and verified task status `completed` with description `时间轴生成完成`.
  - Triggered `POST /api/v1/scripts/1/timeline-pipeline/generate-async`; failure observed as `no_frames_generated_from_audio_timeline` (domain data issue), and **no** `Already running asyncio in this thread` error.

## Next Steps

- Continue `scripts_legacy.py` migration with remaining `storyboard/from-audio-timeline` route extraction.
- Decide whether to generalize loop-safe async runner to other eager-invoked task processors still using direct `anyio.run`.

## Linked Commits

- pending (to be filled by the commit for this change)
