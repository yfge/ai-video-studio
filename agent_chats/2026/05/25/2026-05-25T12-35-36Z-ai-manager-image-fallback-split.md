---
id: 2026-05-25T12-35-36Z-ai-manager-image-fallback-split
date: "2026-05-25T12:35:36Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, image-fallback, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_image_fallback.py
  - ai-pic-backend/tests/unit/test_ai_manager_image_fallback.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split image-to-image text fallback helpers"
---

## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `AIServiceManager` after image reference preload extraction.
- Move image-to-image fallback-to-text-to-image provider inference, fallback
  prompt selection, and success metadata construction out of the manager.
- Preserve the existing fallback behavior and final response shape.

## Changes

- Added `app.services.ai_manager_image_fallback` with provider inference,
  fallback prompt, and fallback execution helpers.
- Replaced the inline image-to-image text fallback block in `AIServiceManager`
  with a helper call.
- Added focused unit tests for provider inference, fallback success metadata,
  task/model type rewriting, and fallback failure error preservation.
- Updated `tasks.md` and the active readiness plan to record the image fallback
  extraction.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_fallback.py ai-pic-backend/tests/unit/test_ai_manager_image_fallback.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_image_fallback.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 11 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_fallback.py ai-pic-backend/tests/unit/test_ai_manager_image_fallback.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-35-36Z-ai-manager-image-fallback-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_fallback.py ai-pic-backend/tests/unit/test_ai_manager_image_fallback.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-35-36Z-ai-manager-image-fallback-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend fallback helper extraction and does not
  change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- The old manager fallback inferred provider hints from model id strings and
  wrote `fallback_from`, `fallback_mode`, and `original_image_url` metadata on
  successful text-to-image fallback responses.
- The helper keeps those semantics and returns the same last-error fields for
  final manager error handling.

## Next Steps

- Continue reducing `AIServiceManager` until the remaining manager code is thin
  provider orchestration.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
