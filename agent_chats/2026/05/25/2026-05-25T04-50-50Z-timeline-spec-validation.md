---
id: 2026-05-25T04-50-50Z-timeline-spec-validation
date: "2026-05-25T04:50:50Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, validation]
related_paths:
  - ai-pic-backend/app/services/timeline_spec_validation.py
  - ai-pic-backend/app/services/timeline_spec_source_validation.py
  - ai-pic-backend/app/services/timeline_spec_validation_types.py
  - ai-pic-backend/app/services/timeline_spec_api_guard.py
  - ai-pic-backend/app/services/timeline_render_hash.py
  - ai-pic-backend/app/services/timeline_import_service.py
  - ai-pic-backend/app/services/timeline_service.py
  - ai-pic-backend/tests/test_timeline_spec_validation.py
  - ai-pic-backend/tests/test_timeline_import_service.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Add Timeline Spec v1 schema and import validation"
---

## User Prompt

按计划继续

## Goals

- Continue Phase 4 of the main-chain commercial readiness plan.
- Validate Timeline Spec v1 structure before create, update, import, and rollback persistence.
- Reject malformed tracks, missing `clip_id`, non-monotonic timing, and invalid source references with actionable errors.
- Keep the next scope focused on clip asset lineage, not APP/SaaS expansion.

## Changes

- Added shared Timeline Spec v1 validators for envelope fields, tracks, clips, timing, source references, and asset references.
- Added an HTTP guard that returns structured 400 details with `code`, `path`, and `message`.
- Wired validation into Timeline create/update, import from `audio_timeline.beats`, and rollback.
- Tightened legacy storyboard import clips so fallback video clips carry stable `scene_id`, `beat_id`, and storyboard source provenance.
- Added validator/API/import tests for malformed tracks, missing `clip_id`, non-monotonic timing, invalid source refs, and missing source audio timeline version.
- Updated active plan and `tasks.md` to mark schema/import validation complete.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_api.py tests/test_timeline_lifecycle_api.py tests/test_timeline_import_service.py tests/test_timeline_spec_validation.py -q`: passed, 15 tests.
- `cd ai-pic-backend && python -m py_compile app/services/timeline_import_service.py app/services/timeline_lifecycle_service.py app/services/timeline_render_hash.py app/services/timeline_service.py app/services/timeline_spec_api_guard.py app/services/timeline_spec_source_validation.py app/services/timeline_spec_validation.py app/services/timeline_spec_validation_types.py app/services/timeline_storyboard_spec_builder.py tests/test_timeline_api.py tests/test_timeline_import_service.py tests/test_timeline_lifecycle_api.py tests/test_timeline_spec_validation.py`: passed.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `git diff --check`: passed.
- `pre-commit run ruff black isort prettier --files <changed files>`: passed after isort import rewrites.
- `wc -l ai-pic-backend/app/services/timeline_service.py`: 249 lines, under the backend service hard limit.
- Backend quick gate is not rerun for this commit because the current broad gate is already blocked by unrelated baseline failures recorded in `2026-05-25T04-31-34Z-timeline-lifecycle.md`; staged pre-commit skips `backend-pytest` for the same documented reason.

## Next Steps

- Add first-class clip asset lineage for source frames, storyboard images, storyboard videos, generated clip videos, and final outputs.
- Link media assets to stable `clip_id` values rather than temporary frame indexes.
- Then implement re-dub, re-cut, and re-render around stable clip identity.

## Linked Commits

- Pending.
