---
id: 2026-05-12T06-34-43Z-timeline-phase2-db-api
date: "2026-05-12T06:34:43Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, timeline, api, migration, render]
related_paths:
  - ai-pic-backend/app/models/timeline.py
  - ai-pic-backend/app/api/v1/endpoints/timelines.py
  - ai-pic-backend/app/services/timeline_service.py
  - ai-pic-backend/tests/test_timeline_api.py
  - docs/exec-plans/active/timeline-main-chain.md
summary: "Implement Timeline Phase 2 DB/API foundation with version locking and render job idempotency"
---

## User Prompt

commit 然后按计划分步实话

## Goals

- Continue after the docs/spec-only timeline baseline commit.
- Implement Phase 2 from `docs/exec-plans/active/timeline-main-chain.md`.
- Keep scope limited to DB/API foundation: timeline persistence, media asset contract, render job enqueue/read API, version lock, access filtering, and tests.
- Do not implement the audio import bridge, real render/export execution, or operator UI in this step.

## Changes

- Added `timelines`, `media_assets`, and `render_jobs` SQLAlchemy models plus Alembic migration `8d1b6e2a4f90`.
- Added timeline schemas, repository layer, service layer, and FastAPI endpoints:
  - `GET /api/v1/episodes/{episode_id}/timelines`
  - `POST /api/v1/episodes/{episode_id}/timelines`
  - `GET /api/v1/timelines/{timeline_id}`
  - `PATCH /api/v1/timelines/{timeline_id}`
  - `POST /api/v1/timelines/{timeline_id}/render`
  - `GET /api/v1/timelines/{timeline_id}/render-jobs`
- Enforced timeline optimistic version locking on update and render queue.
- Added idempotent render enqueue by `timeline_id + timeline_version + render_type + preset_hash`.
- Added story-owner scoped access filtering for non-admin users.
- Updated `tasks.md` and the active timeline exec plan to mark Phase 2 DB/API foundation complete while keeping import bridge, real render/export, rollback/delete, and UI pending.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_api.py`
  - Passed: `2 passed`.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Passed.
- `python scripts/check_repo_contracts.py --mode audit`
  - Passed.
- `git diff --check`
  - Passed.
- `cd ai-pic-backend && alembic heads`
  - Passed: single head `8d1b6e2a4f90`.
- `cd ai-pic-backend && pytest`
  - Failed with 4 unrelated existing script-generation/regeneration failures in `scripts_legacy` paths:
    - `tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run`
    - `tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old`
    - `tests/scripts/test_script_story_structure_sync.py::test_generate_script_syncs_normalized_scenes`
    - `tests/test_api.py::TestScriptAPI::test_generate_script`
  - New timeline API tests passed during the full run.
- `pre-commit run --all-files`
  - Failed due repository-wide existing ruff/template issues and full-repo formatter drift. The automatic formatter changes were reverted because they were outside this task scope.
- `pre-commit run --files <changed files>`
  - Scoped hooks passed through formatting, ruff, docs, contracts, and ledger after this ledger was normalized.
  - Failed at the backend quick pytest hook on the same existing `scripts_legacy` failures:
    - `tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old`
    - `tests/scripts/test_script_story_structure_sync.py::test_generate_script_syncs_normalized_scenes`
- Browser E2E was not run because this step does not change frontend or a user-visible browser workflow.
- Docker production image build was not run after the backend full pytest and pre-commit gates failed on unrelated existing issues.

## Next Steps

- Phase 3: import `audio_timeline.beats` through the existing timeline-pipeline bridge into Timeline Spec v1 clips.
- Generate stable `clip_id` values from `track_type + scene_id + beat_id + ordinal`.
- Add import regression tests for monotonic timing, stable clip ids, and dialogue/video/subtitle clip creation.
- Address existing `scripts_legacy` generation test failures separately before relying on full backend pytest as a clean gate.

## Linked Commits

- `cecba996` docs(timeline): define main chain spec
- Pending: Phase 2 DB/API foundation commit
