---
id: 2026-05-25T11-23-49Z-dialogue-audio-storyboard-split
date: "2026-05-25T11:23:49Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, storyboard, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Move legacy dialogue audio storyboard conversion behind the audio module"
---

## User Prompt

继续，验证时可以使用 3D 或 2D 卡通，避免平台的真人限制

## Goals

- Continue the main-chain readiness plan with an atomic legacy-risk cleanup slice.
- Keep validation away from live-action or realistic human generation paths.
- Preserve backward-compatible imports from `app.services.dialogue_audio_service`.

## Changes

- Removed the duplicate audio-timeline-to-storyboard conversion implementation from
  `app.services.dialogue_audio_service`.
- Re-exported `build_storyboard_frames_from_audio_timeline` and
  `generate_storyboard_from_episode_audio_timeline` from
  `app.services.audio.storyboard_from_timeline` through the historical service
  module for existing callers and tests.
- Replaced the historical service module's direct `db.query(...)` scene/beat
  reads with existing `app.repositories.audio_timeline_repository` helpers, so
  touching the file does not continue widening direct SQLAlchemy access outside
  repositories.
- Updated `tasks.md` and the active main-chain readiness plan to record that only
  the storyboard placeholder conversion slice has moved; scene audio generation,
  episode concatenation, and beats persistence still remain in the historical
  service.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/storyboard_from_timeline.py` -> passed.
- `python -m py_compile ai-pic-backend/app/services/dialogue_audio_service.py` -> passed after repository helper wiring.
- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py tests/unit/services/audio/test_timeline_processor.py -q` -> passed, 35 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-23-49Z-dialogue-audio-storyboard-split.md` -> passed.
- `git diff --check` -> passed.
- `cd ai-pic-backend && python run_tests.py quick` -> did not reach pytest. The runner first executed `pip install -r requirements-test.txt`, and dependency resolution failed under the current Python 3.13 environment because `langchain-core==0.2.43` requires `pydantic>=2.7.4` while the backend pins `pydantic==2.5.0`.
- `pre-commit run --all-files` -> failed on pre-existing repository-wide lint/import issues and attempted EOF normalization across unrelated historical files; those hook side effects were reverted before staging.
- `pre-commit run --files ai-pic-backend/app/services/dialogue_audio_service.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-23-49Z-dialogue-audio-storyboard-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This slice changes backend service module boundaries only and does not
  submit AI image/video generation. The production proof scope remains 2D/3D
  cartoon if later browser/provider validation is needed.

3. Conflict signals and corrections:

- Initial assumption: the storyboard conversion still needed a new module.
- Contradicting evidence: `app.services.audio.storyboard_from_timeline` already
  existed and was exported by `app.services.audio`.
- Reproduction and fix: removed the duplicate legacy implementation and kept
  `dialogue_audio_service` as a compatibility import surface.
- Final verified state: historical imports resolve to the extracted audio module
  implementation.

## Next Steps

- Continue splitting `dialogue_audio_service.py` by moving scene audio generation,
  episode concatenation, and beats persistence into focused `services/audio`
  modules.
- Continue `scripts_legacy.py` and `ai_service_manager.py` risk reduction as
  separate commits.

## Linked Commits

- Pending
