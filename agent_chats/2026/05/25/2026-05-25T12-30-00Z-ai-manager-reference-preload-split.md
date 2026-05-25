---
id: 2026-05-25T12-30-00Z-ai-manager-reference-preload-split
date: "2026-05-25T12:30:00Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, image-to-image, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_image_assets.py
  - ai-pic-backend/tests/unit/test_ai_manager_image_assets.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split image-to-image reference preload helpers"
---

## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `AIServiceManager` after generated image asset extraction.
- Move image-to-image reference download, inline compression, and data URL
  construction out of the manager.
- Keep provider call semantics unchanged: providers still receive
  `kwargs["base64_images"]` when preload succeeds.

## Changes

- Added image reference preload helpers to `app.services.ai_manager_image_assets`.
- Moved HTTPS-to-HTTP download normalization and inline compression out of
  `AIServiceManager`.
- Replaced the inline image-to-image preload block with a helper call that
  returns data URLs for provider payloads.
- Added focused unit tests for HTTPS download normalization, small-payload
  compression passthrough, and data URL preload behavior.
- Updated `tasks.md` and the active readiness plan to record the reference
  preload extraction.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py ai-pic-backend/tests/unit/test_ai_manager_image_assets.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_image_assets.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 11 tests, 2 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py ai-pic-backend/tests/unit/test_ai_manager_image_assets.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-30-00Z-ai-manager-reference-preload-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py ai-pic-backend/tests/unit/test_ai_manager_image_assets.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-30-00Z-ai-manager-reference-preload-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend image-to-image helper extraction and does
  not change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- The old manager path handled local preload failures as warnings so providers
  could still attempt their own URL access or later fallback.
- The helper preserves that behavior by catching full preload failures and
  returning an empty list instead of raising.

## Next Steps

- Continue splitting remaining `AIServiceManager` image-to-image fallback
  provider inference and fallback prompt construction in a separate commit.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
