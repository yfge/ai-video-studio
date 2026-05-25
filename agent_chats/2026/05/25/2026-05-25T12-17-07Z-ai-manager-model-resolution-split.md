---
id: 2026-05-25T12-17-07Z-ai-manager-model-resolution-split
date: "2026-05-25T12:17:07Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, model-resolution, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_model_resolution.py
  - ai-pic-backend/tests/unit/test_ai_manager_model_resolution.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI service manager default model resolution helpers"
---

## User Prompt

commit 然后继续

## Goals

- Continue reducing `AIServiceManager` after failure response extraction.
- Move repeated default model selection for provider calls into a focused helper
  module.
- Keep provider selection, provider invocation, and fallback loops in the
  manager so this remains a narrow refactor.

## Changes

- Added `app.services.ai_manager_model_resolution` with helpers for text,
  text-to-image, image-to-image, and video default model resolution.
- Replaced repeated inline model resolution blocks in `generate_text`,
  `generate_image`, `image_to_image`, and `generate_video` with helper calls.
- Added focused unit tests for requested-model precedence, static model
  precedence, image-to-image text-to-image fallback, image-to-video
  text-to-video fallback, and provider default fallback.
- Updated `tasks.md` and the active readiness plan to record model resolution as
  another completed `ai_service_manager.py` split.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_resolution.py ai-pic-backend/tests/unit/test_ai_manager_model_resolution.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_model_resolution.py tests/unit/test_model_listing.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 21 tests, 2 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_resolution.py ai-pic-backend/tests/unit/test_ai_manager_model_resolution.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-17-07Z-ai-manager-model-resolution-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_resolution.py ai-pic-backend/tests/unit/test_ai_manager_model_resolution.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-17-07Z-ai-manager-model-resolution-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend default-model resolution refactor and
  does not change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- Text, image, image-to-image, and video paths each selected a model inline,
  with slightly different fallback behavior.
- The extraction preserves those distinct fallbacks: image-to-image can fall
  back to text-to-image, and image-to-video can fall back to text-to-video.
- Final targeted tests still cover model listing, image manager behavior,
  provider-prefixed image-to-image errors, style metadata, video model/provider
  behavior, and video task dispatcher error aggregation.

## Next Steps

- Continue splitting remaining `AIServiceManager` fallback loop mechanics in a
  separate commit.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
