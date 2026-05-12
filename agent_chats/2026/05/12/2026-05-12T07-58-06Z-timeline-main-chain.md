---
id: 2026-05-12T07-58-06Z-timeline-main-chain
date: "2026-05-12T07:58:06Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, frontend, timeline, storyboard, production]
related_paths:
  - ai-pic-backend/app/services/script/production_storyboard.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/audio_timeline.py
  - ai-pic-frontend/src/hooks/useEpisodeMetadata.ts
  - docs/exec-plans/active/timeline-main-chain.md
summary: "Wire production script timeline generation into Timeline Spec v1"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 剧本-时间轴-分镜主链修复计划。

## Goals

- Connect default production script generation to Timeline Spec v1.
- Keep deprecated audio/storyboard compatibility paths working while marking
  legacy storyboard support-view output.
- Let the operator timeline workspace prefer persisted Timeline Spec v1 over
  transitional `episodes.extra_metadata.audio_timeline`.
- Correct docs/task-board status so Phase 3 only claims completed work.

## Changes

- `run_auto_timeline_placeholders` now imports generated episode audio timeline
  into Timeline Spec v1 and reports the timeline id/version in production
  metadata.
- Production scene-audio skip logic now requires both current script dialogue
  audio and scene beats before skipping regeneration.
- Deprecated `/audio-timeline/generate-async` now imports existing or newly
  generated audio timeline into Timeline Spec v1.
- Deprecated storyboard-from-audio endpoint now uses the canonical audio
  storyboard builder and marks metadata as a legacy audio-timeline support view.
- Frontend timeline workspace now fetches `/episodes/{episode_id}/timelines`
  and converts the latest matching Timeline Spec dialogue track into the
  existing timeline view, falling back to legacy audio timeline metadata.
- Timeline docs, active exec plan, and task board were updated to match the
  implemented state.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_import_service.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_duration_control_api.py tests/integration/test_audio_storyboard_task_api.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/script/test_production_storyboard_timeline_import.py -q`
  - Passed: 16 passed.
- `cd ai-pic-frontend && npm run lint`
  - Passed with existing warnings, 0 errors.
- `cd ai-pic-frontend && npm run test`
  - Passed: 10 tests.
- `cd ai-pic-frontend && npm run build`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --cached --name-only)`
  - Passed.
- `git diff --cached --check`
  - Passed.
- `pre-commit run --files $(git diff --cached --name-only)`
  - Passed: merge checks, whitespace, EOF, ruff, black, isort, prettier,
    repository docs, repository contracts, agent_chats ledger, frontend lint.
  - Failed: backend quick gate on existing legacy script tests
    `tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old`
    and
    `tests/scripts/test_script_story_structure_sync.py::test_generate_script_syncs_normalized_scenes`.
    Timeline-related backend tests passed in the same run.

## Next Steps

- The synchronous legacy `/api/v1/scripts/generate` 500 remains a separate
  known issue and was not fixed in this Timeline main-chain slice.
- Later Phase 4 should link storyboard frame ids and rendered media assets back
  into Timeline Spec clips/render jobs.

## Linked Commits

- Pending commit for this change set.
