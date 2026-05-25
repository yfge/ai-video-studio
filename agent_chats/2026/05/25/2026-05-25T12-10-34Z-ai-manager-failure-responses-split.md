---
id: 2026-05-25T12-10-34Z-ai-manager-failure-responses-split
date: "2026-05-25T12:10:34Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, fallback, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_failure_responses.py
  - ai-pic-backend/tests/unit/test_ai_manager_failure_responses.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI service manager failure response helpers"
---

## User Prompt

commit 然后继续

## Goals

- Continue reducing `AIServiceManager` after the provider-selection split.
- Move repeated failure response construction into a focused helper module.
- Preserve provider fallback behavior while keeping manager methods as the
  existing orchestration surface.

## Changes

- Added `app.services.ai_manager_failure_responses` with helpers for manager
  failures, provider failures, no-fallback exception responses, provider-prefixed
  errors, and terminal fallback failures.
- Replaced repeated `AIResponse(success=False, ...)` construction in text, image,
  image-to-image, video, and TTS fallback paths with helper calls.
- Added focused unit tests for manager fallback provider identity, provider error
  prefixing, and terminal fallback response selection.
- Updated `tasks.md` and the active readiness plan to record the failure
  response extraction as another completed `ai_service_manager.py` slice.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_failure_responses.py ai-pic-backend/tests/unit/test_ai_manager_failure_responses.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_failure_responses.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 12 tests, 2 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_failure_responses.py ai-pic-backend/tests/unit/test_ai_manager_failure_responses.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-10-34Z-ai-manager-failure-responses-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_failure_responses.py ai-pic-backend/tests/unit/test_ai_manager_failure_responses.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-10-34Z-ai-manager-failure-responses-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend failure-response refactor and does not
  change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- The manager had repeated response construction across no-provider,
  no-fallback exception, and terminal fallback paths.
- The extraction keeps fallback loops and provider calls in the manager; only
  response creation and provider error prefixing moved to the helper module.
- The targeted tests still cover image payload normalization, image-to-image
  error reporting, style metadata, video model/provider behavior, and video task
  dispatcher error aggregation.

## Next Steps

- Continue splitting remaining `AIServiceManager` provider routing/fallback loop
  mechanics in a separate commit.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
