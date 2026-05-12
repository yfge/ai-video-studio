---
id: 2026-05-12T06-50-53Z-timeline-phase3-import-bridge
date: "2026-05-12T06:50:53Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, import, audio, pipeline]
related_paths:
  - ai-pic-backend/app/services/timeline_import_service.py
  - ai-pic-backend/app/services/timeline_spec_builder.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/timeline_pipeline.py
  - ai-pic-backend/tests/integration/test_timeline_pipeline_import_api.py
  - docs/exec-plans/active/timeline-main-chain.md
summary: "Import audio_timeline beats into Timeline Spec v1 from the pipeline bridge"
---

## User Prompt

commit 然后按计划分步实话

## Goals

- Continue after Phase 2 DB/API foundation.
- Implement Phase 3 only: bridge `audio_timeline.beats` into persisted Timeline Spec v1.
- Generate stable clip ids from `track_type + scene_id + beat_id + ordinal`.
- Keep real render/export execution and operator UI out of scope.

## Changes

- Added `timeline_import_service` to build Timeline Spec v1 from
  `episodes.extra_metadata.audio_timeline`.
- Split the spec building and stable clip-id rules into
  `timeline_spec_builder` so the import service stays inside repository size
  limits.
- The generated spec now includes minimum `dialogue`, `video`, and `subtitle`
  tracks, monotonic clip timing, source refs, episode audio refs, and storyboard
  support-view metadata.
- Extended timeline pipeline Step 2 to upsert a `timelines` row after generating
  or reusing the transition `audio_timeline`.
- Added repository lookup for latest timeline by `episode_id + script_id`.
- Removed direct SQLAlchemy queries from the touched timeline-pipeline endpoint
  by using repository helpers for task, user, and beat lookup.
- Updated the active exec plan and `tasks.md` to mark Phase 3 import bridge
  complete while leaving real render/export and UI pending.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_import_service.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_duration_control_api.py::test_process_dialogue_audio_task_uses_duration_control`
  - Passed: `4 passed`.
- `cd ai-pic-backend && ruff check app/services/timeline_import_service.py app/services/timeline_spec_builder.py app/repositories/audio_timeline_repository.py app/repositories/user_repository.py app/repositories/timeline_repository.py app/api/v1/endpoints/scripts/timeline_pipeline.py tests/test_timeline_import_service.py tests/integration/test_duration_control_api.py tests/integration/test_timeline_pipeline_import_api.py`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Passed after splitting the oversized files and removing direct-query/legacy-reference drift from changed files.
- `git diff --check`
  - Passed.
- Browser E2E was not run because Phase 3 is a backend import bridge with no frontend route or browser workflow change.

## Next Steps

- Phase 4: link existing storyboard image/video outputs to `media_assets`.
- Render proxy/final outputs from a locked timeline version and persist outputs
  as `render_jobs.output_asset_id`.
- Add retry/idempotency tests proving completed outputs do not mutate older
  timeline versions.

## Linked Commits

- `168f39c7` feat(timeline): add main chain db api foundation
- Pending: Phase 3 import bridge commit
