---
id: 2026-05-25T04-31-34Z-timeline-lifecycle
date: "2026-05-25T04:31:34Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, lifecycle, rollback]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/app/services/timeline_lifecycle_service.py
  - ai-pic-backend/app/services/timeline_revision_service.py
  - ai-pic-backend/app/models/timeline.py
  - ai-pic-backend/alembic/versions/a4f5c6d7e8f9_add_timeline_revisions_and_lifecycle.py
  - ai-pic-backend/tests/test_timeline_lifecycle_api.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Add Timeline delete, restore, rollback, and render-attempt lifecycle APIs"
---

## User Prompt

按计划继续

## Goals

- Continue Phase 3 of the main-chain commercial readiness plan.
- Add safe Timeline delete/restore behavior without hard-deleting render outputs.
- Add rollback to an earlier Timeline version with stale-version protection.
- Keep render jobs traceable after rollback.

## Changes

- Added `timeline_revisions` snapshots and Timeline rollback state columns.
- Recorded Timeline version snapshots on create and update.
- Added lifecycle APIs for Timeline delete, restore, and rollback.
- Added render job delete and restore APIs using the existing soft-delete pattern.
- Added rollback state and soft-delete fields to Timeline and render job API responses.
- Added revision recording to `audio_timeline` import create/update paths.
- Updated active planning docs and the compact DB schema summary.

## Validation

- `cd ai-pic-backend && python -m py_compile app/api/v1/endpoints/timelines.py app/models/timeline.py app/repositories/timeline_repository.py app/schemas/timeline.py app/services/timeline_import_service.py app/services/timeline_lifecycle_service.py app/services/timeline_responses.py app/services/timeline_revision_service.py app/services/timeline_service.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py alembic/versions/a4f5c6d7e8f9_add_timeline_revisions_and_lifecycle.py`: passed.
- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_lifecycle_api.py tests/test_timeline_import_service.py -q`: passed, 8 tests.
- `cd ai-pic-backend && alembic heads`: passed, head is `a4f5c6d7e8f9`.
- Temp SQLite `alembic upgrade head`: failed before reaching this migration because existing migration `e5f3948ee82e` uses SQLite-incompatible `ALTER TABLE images ALTER COLUMN filename TYPE VARCHAR(255)`.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `git diff --check`: passed.
- `pre-commit run ruff black isort prettier --files <changed files>`: passed after formatter rewrites.
- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts -q`: failed on existing unrelated baseline tests: `tests/unit/test_dialogue_audio_service.py::test_audio_timeline_storyboard_prompt_description_blurs_readable_text`, `tests/unit/test_storyboard_prompt_templates.py::test_storyboard_audio_visual_prompt_templates_exist`, and `tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old`. The first two expect the older prompt phrase `屏幕文字模糊不可读`; the current prompt uses `屏幕/纸面内容只能模糊呈现`. The script regeneration failure leaves the prior script active.

## Next Steps

- Add Timeline Spec schema/import validation.
- Reject malformed tracks, missing `clip_id`, non-monotonic timing, and invalid source references before persistence.
- Keep first-class clip asset lineage as the next production stability boundary after validation.

## Linked Commits

- Pending.
