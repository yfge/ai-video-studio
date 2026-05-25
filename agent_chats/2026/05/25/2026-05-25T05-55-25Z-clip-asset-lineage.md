---
id: 2026-05-25T05-55-25Z-clip-asset-lineage
date: "2026-05-25T05:55:25Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, media-assets, lineage]
related_paths:
  - ai-pic-backend/app/models/timeline.py
  - ai-pic-backend/alembic/versions/c5e6f7a8b9c0_add_timeline_clip_assets.py
  - ai-pic-backend/app/services/timeline_clip_asset_lineage.py
  - ai-pic-backend/app/services/timeline_clip_asset_candidates.py
  - ai-pic-backend/app/services/render/timeline_render_output.py
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/tests/test_timeline_api.py
  - ai-pic-backend/tests/test_timeline_import_service.py
  - ai-pic-backend/tests/unit/services/render/test_timeline_render_service.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Add first-class Timeline clip asset lineage"
---

## User Prompt

继续

## Goals

- Continue Phase 5 of the main-chain commercial readiness plan.
- Add a first-class backend lineage layer from stable Timeline `clip_id` values to source and output media assets.
- Avoid expanding APP/SaaS/social directions.
- Keep this commit focused on backend lineage infrastructure, not rework UI.

## Changes

- Added `timeline_clip_assets` with timeline version, stable `clip_id`, asset role, media asset, render job, source metadata, and replacement hook fields.
- Added repository and service support to sync source assets from Timeline Spec clips.
- Wired Timeline create/update, `audio_timeline` import, rollback, and render output persistence into clip asset lineage.
- Added `GET /api/v1/timelines/{timeline_id}/clip-assets` for backend asset audit views.
- Added source audio, legacy storyboard video, and render output lineage tests.
- Updated active plan, `tasks.md`, and compact DB schema notes.

## Validation

- `cd ai-pic-backend && python -m py_compile app/api/v1/endpoints/timelines.py app/models/timeline.py app/models/__init__.py app/repositories/timeline_repository.py app/schemas/timeline.py app/services/render/timeline_render_output.py app/services/timeline_clip_asset_candidates.py app/services/timeline_clip_asset_lineage.py app/services/timeline_import_service.py app/services/timeline_lifecycle_service.py app/services/timeline_render_dispatch.py app/services/timeline_responses.py app/services/timeline_service.py tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py alembic/versions/c5e6f7a8b9c0_add_timeline_clip_assets.py`: passed.
- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py tests/unit/services/render/test_timeline_render_service.py -q`: passed, 20 tests.
- `cd ai-pic-backend && alembic heads`: passed, head is `c5e6f7a8b9c0`.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `git diff --check`: passed.
- `pre-commit run ruff black isort prettier --files <changed files>`: passed after formatter import rewrites.
- Backend quick gate is not rerun for this commit because the current broad gate is already blocked by unrelated baseline failures recorded in `2026-05-25T04-31-34Z-timeline-lifecycle.md`; staged pre-commit skips `backend-pytest` for the same documented reason.

## Next Steps

- Implement re-dub, re-cut, and re-render operations around stable `clip_id`.
- Preserve original `clip_id` while adding replacement lineage through `replacement_of_id`.
- Extend operator UI to read `clip-assets` for source/output/replacement audit.

## Linked Commits

- Pending.
