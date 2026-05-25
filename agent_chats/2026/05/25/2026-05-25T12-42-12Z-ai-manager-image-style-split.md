---
id: 2026-05-25T12-42-12Z-ai-manager-image-style-split
date: "2026-05-25T12:42:12Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, image-style, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_image_style.py
  - ai-pic-backend/tests/unit/test_ai_manager_image_style.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split image style resolution helpers"
---

## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `AIServiceManager` after image fallback extraction.
- Move text-to-image and image-to-image style spec resolution out of the
  manager.
- Preserve prompt injection, OpenAI style derivation, and response metadata.

## Changes

- Added `app.services.ai_manager_image_style` with text-to-image and
  image-to-image style resolution helpers.
- Moved style prompt injection, legacy style derivation, OpenAI style
  derivation, and style metadata attachment behind helper calls.
- Added focused unit tests for style prompt injection, image-to-image empty
  prompt handling, and metadata no-op behavior.
- Updated `tasks.md` and the active readiness plan to record the image style
  extraction.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_style.py ai-pic-backend/tests/unit/test_ai_manager_image_style.py` -> passed.
- Initial targeted pytest found the new helper test expected `cartoon`, while
  the existing style utility derives `portrait` for `romance_anime_soft`.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_image_style.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_ai_manager_image_fallback.py tests/unit/test_ai_service_manager_image_to_image_error.py -q` -> passed after correcting the test expectation, 7 tests, 1 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_style.py ai-pic-backend/tests/unit/test_ai_manager_image_style.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-42-12Z-ai-manager-image-style-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_style.py ai-pic-backend/tests/unit/test_ai_manager_image_style.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-42-12Z-ai-manager-image-style-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend style resolution helper extraction and
  does not change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- Style utility derivation is the source of truth for legacy style aliases.
- The manager still controls provider calls and only receives resolved prompt,
  legacy style, OpenAI override style, and response metadata inputs.

## Next Steps

- Continue reducing remaining `AIServiceManager` provider call loops only where
  behavior can stay covered by targeted tests.
- Continue reducing `dialogue_audio_service.py` scene-level TTS orchestration.

## Linked Commits

- Pending
