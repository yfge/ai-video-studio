## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `ai_service_manager.py` with a focused TTS fallback
  extraction.
- Keep speech provider selection, logging, fallback, and terminal error behavior
  unchanged.

## Changes

- Added `app.services.ai_manager_tts_generation`.
- Moved `AIServiceManager.text_to_speech` fallback orchestration into
  `text_to_speech_with_fallback`.
- Kept `AIServiceManager.text_to_speech` as the public wrapper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  TTS split.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_tts_generation.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_providers_http_exception_passthrough.py tests/unit/test_dialogue_audio_service.py -q`
  - Passed: 15 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_tts_generation.py`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_tts_generation.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-33-22Z-ai-manager-tts-generation.md`
  - Passed; backend quick gate passed inside the hook.

## Next Steps

- Continue extracting remaining text and image generation fallback loops from
  `ai_service_manager.py`.

## Linked Commits

Pending
