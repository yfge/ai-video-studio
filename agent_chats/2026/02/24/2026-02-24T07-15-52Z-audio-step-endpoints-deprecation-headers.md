---
id: 2026-02-24T07-15-52Z-audio-step-endpoints-deprecation-headers
date: 2026-02-24T07:15:52Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [backend, api, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py
  - ai-pic-backend/tests/integration/test_duration_control_api.py
  - ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py
  - tasks.md
summary: "Marked step-by-step audio/timeline/storyboard endpoints deprecated via OpenAPI + response headers and added integration coverage."
---

## User Prompt

继续

## Goals

- Complete the pending deprecate marking for migrated step-by-step script audio endpoints.
- Keep behavior unchanged while exposing explicit migration guidance to one-click timeline pipeline endpoint.
- Add test coverage and finish all required validation gates.

## Changes

- Added shared deprecation header helper in `ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py`:
  - `mark_pipeline_endpoint_deprecated(response, successor_path=...)`
  - standard headers: `Deprecation`, `Sunset`, `Link`, `X-API-Deprecated`.
- Marked these routes as `deprecated=True` in OpenAPI and wired response headers:
  - `POST /api/v1/scripts/{script_id}/dialogue-audio/generate-async`
  - `POST /api/v1/scripts/{script_id}/audio-timeline/generate-async`
  - `POST /api/v1/scripts/{script_id}/storyboard/from-audio-timeline/generate-async`
- Added/updated integration assertions for deprecation headers:
  - `ai-pic-backend/tests/integration/test_duration_control_api.py`
  - `ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py`
- Updated `tasks.md` to mark this deprecate-marking task as completed.

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts/audio_pipeline_utils.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py ai-pic-backend/app/api/v1/endpoints/scripts/audio_storyboard.py ai-pic-backend/tests/integration/test_duration_control_api.py ai-pic-backend/tests/integration/test_audio_storyboard_task_api.py tasks.md`
  - passed.
- `cd ai-pic-backend && pytest tests/integration/test_duration_control_api.py tests/integration/test_audio_storyboard_task_api.py`
  - passed (`6 passed`).
- `cd ai-pic-backend && pytest`
  - first run had 1 unrelated flaky failure (`tests/test_story_generation_fallback.py` expected `ai_fallback` but got `ai_fallback_invalid`).
  - reran targeted flaky test: passed.
  - reran full suite: passed (`1889 passed, 87 skipped`).
- `./docker/build_prod_images.sh`
  - passed with tag `9939f44`.
- Chrome E2E (lite stack):
  - opened `http://localhost:8089/episodes/1/storyboard`, clicked `从时间轴同步分镜占位`, task executed and storyboard version incremented.
  - inspected network response for `POST /api/v1/scripts/1/storyboard/from-audio-timeline/generate-async` and confirmed headers:
    - `deprecation: true`
    - `sunset: Thu, 31 Dec 2026 23:59:59 GMT`
    - `link: </api/v1/scripts/1/timeline-pipeline/generate-async>; rel="successor-version"`
    - `x-api-deprecated: Use timeline-pipeline endpoint`
- HTTP request-level spot checks (curl) confirmed the same headers for:
  - `dialogue-audio/generate-async`
  - `audio-timeline/generate-async`
  - `storyboard/from-audio-timeline/generate-async`

## Next Steps

- Optionally show deprecation notice in frontend UI when these endpoints are called (so operators know to migrate workflow entry).
- Continue reducing `scripts_legacy.py` by migrating remaining non-audio endpoints.

## Linked Commits

- (pending)
