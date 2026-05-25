---
id: 2026-05-25T11-34-17Z-dialogue-audio-episode-builder-split
date: "2026-05-25T11:34:17Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, timeline, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Move legacy episode audio timeline helpers behind audio modules"
---

## User Prompt

继续，验证时可以使用 3D 或 2D 卡通，避免平台的真人限制

## Goals

- Continue reducing `dialogue_audio_service.py` without changing scene-level TTS
  behavior.
- Keep historical imports compatible while moving episode-level audio timeline
  logic to focused `services/audio` modules.
- Keep validation limited to local backend checks; no live-action provider
  generation is involved.

## Changes

- Re-exported `generate_episode_audio_timeline` from
  `app.services.audio.episode_audio_builder` through the historical
  `app.services.dialogue_audio_service` module.
- Re-exported `build_episode_timeline_beats` from
  `app.services.audio.episode_timeline_beats` through the same compatibility
  surface.
- Removed the duplicate episode timeline beat construction and episode audio
  concatenation/persistence implementation from `dialogue_audio_service.py`.
- Updated `tasks.md` and the active readiness plan to mark this split slice done
  while leaving scene-level TTS generation and beat persistence as remaining
  `dialogue_audio_service.py` work.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/episode_audio_builder.py ai-pic-backend/app/services/audio/episode_timeline_beats.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py tests/unit/services/audio/test_timeline_processor.py -q` -> passed, 35 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-34-17Z-dialogue-audio-episode-builder-split.md` -> passed.
- `git diff --check` -> passed after removing a trailing blank line at EOF.
- `pre-commit run --files ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-34-17Z-dialogue-audio-episode-builder-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is a backend module-boundary cleanup and does not change a
  user-visible frontend/backend flow or submit image/video generation.

3. Conflict signals and corrections:

- Initial assumption: only storyboard placeholder conversion remained duplicated.
- Contradicting evidence: `episode_audio_builder.py` and
  `episode_timeline_beats.py` already existed, but `dialogue_audio_service.py`
  still held duplicate compatibility implementations.
- Reproduction and fix: replaced the duplicate functions with compatibility
  imports and reran the dialogue/audio timeline unit tests.
- Final verified state: old imports resolve to the focused audio modules.

## Next Steps

- Move scene-level beat persistence and scene metadata writeback behind
  `app.services.audio.scene_audio_persistence`.
- Continue reducing `scripts_legacy.py` and `ai_service_manager.py` in separate
  commits.

## Linked Commits

- Pending
