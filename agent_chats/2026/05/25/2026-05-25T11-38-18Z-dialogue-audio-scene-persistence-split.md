---
id: 2026-05-25T11-38-18Z-dialogue-audio-scene-persistence-split
date: "2026-05-25T11:38:18Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, persistence, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Move scene audio persistence calls behind the audio persistence module"
---

## User Prompt

继续，验证时可以使用 3D 或 2D 卡通，避免平台的真人限制

## Goals

- Continue the `dialogue_audio_service.py` split without changing TTS generation
  orchestration.
- Route scene beat persistence, scene audio metadata writeback, and duration
  logging through the existing focused audio persistence module.
- Keep validation local and avoid provider video/image generation.

## Changes

- Replaced inline per-scene duration validation in `dialogue_audio_service.py`
  with `app.services.audio.scene_audio_persistence.validate_duration`.
- Replaced inline scene beat soft-delete/reinsert logic with
  `scene_audio_persistence.persist_beats`.
- Replaced inline scene dialogue audio metadata writeback with
  `scene_audio_persistence.update_scene_metadata`.
- Updated `tasks.md` and the active readiness plan to record that scene beat
  persistence and metadata writeback are split; scene-level TTS orchestration
  remains in the historical service.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/scene_audio_persistence.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py tests/unit/services/audio/test_timeline_processor.py -q` -> passed, 35 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-38-18Z-dialogue-audio-scene-persistence-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-38-18Z-dialogue-audio-scene-persistence-split.md` -> passed after isort reordered the new import group.

2. Browser or MCP validation:

- Not run. This is a backend persistence-boundary cleanup and does not change a
  user-visible flow or submit image/video generation.

3. Conflict signals and corrections:

- Initial assumption: the remaining split target was mostly scene TTS generation.
- Contradicting evidence: beat persistence and scene metadata writeback were
  still inline even though `scene_audio_persistence.py` already existed.
- Reproduction and fix: moved those calls behind the existing module and reran
  the dialogue/audio timeline unit tests.
- Final verified state: `dialogue_audio_service.py` now delegates scene
  persistence and metadata writeback to `services/audio`.

## Next Steps

- Split the remaining scene-level TTS generation orchestration from
  `dialogue_audio_service.py` if a low-risk boundary is available.
- Continue reducing `scripts_legacy.py` and `ai_service_manager.py` in separate
  commits.

## Linked Commits

- Pending
