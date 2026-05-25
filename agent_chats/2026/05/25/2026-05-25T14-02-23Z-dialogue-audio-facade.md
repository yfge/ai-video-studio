## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue P1 stability cleanup by reducing the historical
  `dialogue_audio_service.py` surface.
- Preserve older imports used by tests while routing production scene/episode
  audio behavior to the split `app.services.audio.*` modules.

## Changes

- Replaced `app.services.dialogue_audio_service` with a thin compatibility
  facade.
- Re-exported scene audio generation, episode audio timeline, episode beats, and
  storyboard timeline helpers from their split `app.services.audio.*` modules.
- Moved historical fixed segment planning compatibility into
  `app.services.audio.dialogue_service_compat`.
- Moved historical dialogue text cleanup compatibility into
  `app.services.audio.dialogue_service_text_compat`.
- Updated `tasks.md` and the active commercial readiness plan to mark the
  `dialogue_audio_service.py` split complete.

## Validation

- `python -m py_compile ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/dialogue_service_compat.py ai-pic-backend/app/services/audio/dialogue_service_text_compat.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py tests/unit/services/audio/test_dialogue_processor.py tests/unit/services/audio/test_timeline_processor.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py -q`
  - Passed: 81 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/dialogue_service_compat.py ai-pic-backend/app/services/audio/dialogue_service_text_compat.py`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/dialogue_service_compat.py ai-pic-backend/app/services/audio/dialogue_service_text_compat.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-02-23Z-dialogue-audio-facade.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/dialogue_audio_service.py ai-pic-backend/app/services/audio/dialogue_service_compat.py ai-pic-backend/app/services/audio/dialogue_service_text_compat.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-02-23Z-dialogue-audio-facade.md`
  - Passed.

## Next Steps

- Continue P1 cleanup on `scripts_legacy.py`.
- Keep P2 sample proof pending until remaining legacy router risk is reduced.

## Linked Commits

Pending
