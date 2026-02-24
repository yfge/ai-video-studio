---
id: 2026-02-24T07-01-02Z-scripts-audio-storyboard-migration
date: 2026-02-24T07:01:02Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [backend, scripts, refactor, e2e]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py
  - tasks.md
summary: "Migrated storyboard-from-audio-timeline route/worker out of scripts_legacy, added integration tests, and verified end-to-end in Chrome lite mode."
---

## User Prompt

继续

## Goals

- Continue decommissioning `scripts_legacy.py` by extracting the remaining storyboard-from-audio-timeline endpoint and task processor into modular scripts endpoints.
- Reuse shared helpers for auth/access, task progress, and eager async-loop compatibility.
- Add regression tests and complete full validation gates, including Chrome E2E.

## Changes

- Added new module `ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py`:
  - `POST /api/v1/scripts/{script_id}/storyboard/from-audio-timeline/generate-async`
  - `_process_script_audio_storyboard_task`
  - request schema `ScriptAudioStoryboardGenerateRequest`
- Wired new router/processor in `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py` and removed legacy import of `_process_script_audio_storyboard_task` from `scripts_legacy.py`.
- Extended shared access guard in `ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py`:
  - `load_script_with_access` now also filters soft-deleted `Script/Episode/Story`.
- Removed migrated storyboard route/processor and related dead imports/helpers from `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`.
- Added integration tests in `ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py`:
  - task queueing route
  - worker processor completion path
- Updated `tasks.md` progress notes:
  - marked storyboard/from-audio-timeline migration complete in this phase
  - updated `scripts_legacy.py` line-count progress to 4323 and deprecate-marker pending note.

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py tasks.md`
  - first run auto-fixed EOF newline in `scripts_legacy.py`; second run fully passed.
- `cd ai-pic-backend && pytest`
  - passed: `1888 passed, 87 skipped`.
- `./docker/build_prod_images.sh`
  - passed (backend/frontend multi-arch images built and pushed with tag `aabe48f`).
- Chrome E2E (lite stack, real browser path):
  - Started lite stack: `cd docker && docker compose --env-file .env.lite -f docker-compose.lite.yml up -d --build`
  - Logged in with required account: `geyunfei / Gyf@845261` at `http://localhost:8089/login`
  - Opened `http://localhost:8089/episodes/1/storyboard`
  - Clicked `从时间轴同步分镜占位`
  - Observed task creation dialog: `task_id=1`
  - Confirmed page updated to `当前分镜帧总数：3` and `来源：audio_timeline`
  - Verified task API: `/api/v1/tasks/1` => `status=completed`, `error_message=null`, `result_file_path=script:1:storyboard_from_audio_timeline`
- Conflict handling / correction record:
  - During E2E data setup, manual seed rows initially caused 500s.
  - Instead of assuming environment issues, checked backend logs and fixed concrete root causes:
    - invalid JSON in `episodes.extra_metadata`
    - missing required response fields (`status/created_at/updated_at/is_public/format_type/language/version`).
  - Re-validated API endpoints and completed E2E only after real requests passed.

## Next Steps

- Add explicit `deprecated` markers/headers for migrated legacy routes still served by `scripts_legacy.py`.
- Continue extracting remaining script timeline/storyboard helper logic into dedicated modules to reduce `scripts_legacy.py` further.

## Linked Commits

- (pending)
