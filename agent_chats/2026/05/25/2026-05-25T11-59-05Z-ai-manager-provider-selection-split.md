---
id: 2026-05-25T11-59-05Z-ai-manager-provider-selection-split
date: "2026-05-25T11:59:05Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, provider-selection, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_provider_selection.py
  - ai-pic-backend/tests/unit/test_ai_manager_provider_selection.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI service manager provider selection helpers"
---

## User Prompt

commit 然后继续

## Goals

- Continue reducing `AIServiceManager` after the model cache split.
- Move provider rate-limit checks, priority/weight selection, and request-count
  updates to a focused helper module.
- Preserve manager method names and selection semantics for existing callers.

## Changes

- Added `app.services.ai_manager_provider_selection` with provider rate-limit,
  explicit preference, priority selection, weighted selection, and request count
  helpers.
- Changed `AIServiceManager._check_rate_limit`, `_select_provider`,
  `_select_by_priority`, `_select_by_weight`, and `_update_request_count` into
  thin wrappers around the helper module.
- Added focused unit tests for explicit provider preference, priority fallback,
  weighted selection, rate-limit reset, and request-count increments.
- Updated `tasks.md` and the active readiness plan to record provider selection
  as the next extracted `ai_service_manager.py` slice.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_selection.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_provider_selection.py tests/unit/test_model_listing.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 21 tests, 2 skipped.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_selection.py ai-pic-backend/tests/unit/test_ai_manager_provider_selection.py` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_selection.py ai-pic-backend/tests/unit/test_ai_manager_provider_selection.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-59-05Z-ai-manager-provider-selection-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_selection.py ai-pic-backend/tests/unit/test_ai_manager_provider_selection.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-59-05Z-ai-manager-provider-selection-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend provider-selection refactor and does not
  change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- Initial selection logic lived inline in `ai_service_manager.py` and depended
  on `random` plus an inline `time` import.
- Extraction kept the manager wrappers in place and moved randomness/time access
  to the helper module, making the unit tests deterministic via monkeypatching.
- Final verified state: model listing, image manager, video model selection, and
  video dispatcher tests still pass.

## Next Steps

- Continue splitting `AIServiceManager` fallback loops in a separate commit.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
