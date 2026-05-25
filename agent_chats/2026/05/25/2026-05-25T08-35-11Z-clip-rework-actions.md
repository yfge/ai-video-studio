---
id: 2026-05-25T08-35-11Z-clip-rework-actions
date: "2026-05-25T08:35:11Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, media-assets, rework]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/app/repositories/timeline_repository.py
  - ai-pic-backend/app/schemas/timeline.py
  - ai-pic-backend/app/services/timeline_clip_rework_service.py
  - ai-pic-backend/tests/test_timeline_api.py
  - ai-pic-backend/tests/test_timeline_clip_rework_api.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - tasks.md
summary: "Add stable clip-id rework replacement actions"
---

## User Prompt

继续

## Goals

- Continue Phase 5 of the main-chain commercial readiness plan after first-class
  clip asset lineage landed.
- Add backend re-dub, re-cut, and re-render actions that preserve stable
  Timeline `clip_id` values.
- Keep the boundary focused on replacement lineage, not operator UI or real
  provider/render orchestration.

## Changes

- Added `TimelineClipReworkRequest` and
  `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework`.
- Added `TimelineClipReworkService` to validate timeline version, current clip
  existence, media asset type, and supported action/role combinations.
- Recorded rework assets as `timeline_clip_assets` rows with
  `source=operator_rework`, stable `clip_id`, and `replacement_of_id` history.
- Covered `re_dub`, `re_cut`, `re_render`, stale version, and missing clip API
  behavior in a focused Timeline clip rework API test module.
- Updated `tasks.md` and active execution plans to mark only the backend rework
  API as done while leaving operator UI, real generation orchestration, and
  production samples pending.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/timelines.py ai-pic-backend/app/repositories/timeline_repository.py ai-pic-backend/app/schemas/timeline.py ai-pic-backend/app/services/timeline_clip_rework_service.py ai-pic-backend/tests/test_timeline_api.py ai-pic-backend/tests/test_timeline_clip_rework_api.py`: passed.
- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_clip_rework_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py -q`: passed, 23 tests.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `git diff --check`: passed.
- `pre-commit run ruff black isort prettier --files <changed files>`: passed.
- Broad backend quick/full gate is not rerun for this commit because the current
  broad gate is already blocked by unrelated baseline failures recorded in
  `2026-05-25T04-31-34Z-timeline-lifecycle.md`; staged pre-commit skips
  `backend-pytest` for the same documented reason.

## Next Steps

- Wire rework actions into operator UI and provider/render orchestration.
- Add an operator asset audit view that shows source, output, and replacement
  history for a selected clip.
- Continue toward the 10 narrow vertical sample production proof.

## Linked Commits

- Pending.
