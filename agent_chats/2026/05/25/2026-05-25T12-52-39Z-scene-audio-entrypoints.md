---
id: 2026-05-25T12-52-39Z-scene-audio-entrypoints
date: "2026-05-25T12:52:39Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, timeline, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/duration_controlled_dialogue_service.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py
  - ai-pic-backend/app/services/audio/scene_audio_generator.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Route scene dialogue audio entry points to modular generator"
---

## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing production reliance on `dialogue_audio_service.py`.
- Route remaining production scene dialogue audio callers to the modular
  `app.services.audio.scene_audio_generator`.
- Preserve the historical service as a compatibility surface for existing tests
  and helper imports.

## Changes

- Updated duration-controlled dialogue generation to import
  `generate_scene_dialogue_audio` from `app.services.audio.scene_audio_generator`.
- Updated the deprecated dialogue-audio endpoint to use the same modular scene
  generator.
- Moved the duration-control per-scene generation loop into
  `app.services.duration_controlled_scene_runner` so the touched service stays
  under repository file-size limits.
- Replaced touched endpoint direct `.query(...)` calls with existing repository
  helpers for task, user, and scene beat lookup.
- Updated `tasks.md` and the active readiness plan to record that these
  production entry points no longer call the historical dialogue audio service.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/duration_controlled_dialogue_service.py ai-pic-backend/app/services/duration_controlled_scene_runner.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py tests/unit/services/script/test_production_storyboard_timeline_import.py -q` -> passed, 11 tests.
- Initial `python scripts/check_repo_contracts.py --mode diff ...` failed because touching historical duration-control and deprecated endpoint files re-enabled existing oversized/direct-query checks.
- After splitting the duration-control scene runner and replacing direct endpoint queries, `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/duration_controlled_dialogue_service.py ai-pic-backend/app/services/duration_controlled_scene_runner.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-52-39Z-scene-audio-entrypoints.md` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/duration_controlled_dialogue_service.py ai-pic-backend/app/services/duration_controlled_scene_runner.py ai-pic-backend/app/api/v1/endpoints/scripts/dialogue_audio.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-52-39Z-scene-audio-entrypoints.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend import-route cleanup and does not change
  a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- `production_storyboard.py` and `timeline_pipeline.py` were already using the
  modular scene generator.
- After this change, app code no longer imports
  `generate_scene_dialogue_audio` from the historical service; tests still use
  the old module for compatibility helper coverage.

## Next Steps

- Continue reducing `dialogue_audio_service.py` by moving remaining compatibility
  helper tests to their owning modules or re-exporting from the historical
  module.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
