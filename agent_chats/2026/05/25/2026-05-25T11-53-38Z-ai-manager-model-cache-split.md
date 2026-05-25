---
id: 2026-05-25T11-53-38Z-ai-manager-model-cache-split
date: "2026-05-25T11:53:38Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, model-cache, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_model_cache.py
  - ai-pic-backend/tests/unit/test_model_listing.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI service manager model-list cache helpers"
---

## User Prompt

commit 然后继续

## Goals

- Continue P1 stability work after confirming the worktree was already clean.
- Move model-list cache details out of `AIServiceManager` without changing
  provider enumeration, model filtering, or fallback behavior.
- Add focused coverage for cache keying and copy semantics.

## Changes

- Added `app.services.ai_manager_model_cache` with helpers for model cache keys,
  cache lookup, and cache writes.
- Updated `AIServiceManager.list_models` to delegate cache behavior to the new
  helper module while preserving the existing `_models_cache` compatibility
  field.
- Added unit tests for cache key formatting, disabled-cache behavior, and
  returning copies instead of mutable cache internals.
- Updated `tasks.md` and the active readiness plan to record the model cache
  extraction.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_cache.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_model_listing.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 16 tests, 2 skipped.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_cache.py ai-pic-backend/tests/unit/test_model_listing.py` -> passed after keeping `ai_service_manager.py` below the current baseline exemption.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_cache.py ai-pic-backend/tests/unit/test_model_listing.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-53-38Z-ai-manager-model-cache-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_cache.py ai-pic-backend/tests/unit/test_model_listing.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-53-38Z-ai-manager-model-cache-split.md` -> passed after black/isort formatted the new cache helper imports.

2. Browser or MCP validation:

- Not run. This is an internal backend model-list cache refactor and does not
  change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- Initial contract run failed because `ai_service_manager.py` exceeded its
  baseline exemption by 1 line.
- Correction: switched the cache helper import to a module alias and reran the
  contract check.
- Final verified state: model-list tests pass and diff-mode contracts pass.

## Next Steps

- Continue splitting `AIServiceManager` provider selection/fallback in a separate
  commit.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
