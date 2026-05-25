## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `ai_service_manager.py` by extracting the text generation
  fallback loop.
- Preserve provider pinning, default model resolution, JSON/schema pass-through,
  logging, and fallback behavior.

## Changes

- Added `app.services.ai_manager_text_generation`.
- Moved `AIServiceManager.generate_text` fallback orchestration into
  `generate_text_with_fallback`.
- Kept `AIServiceManager.generate_text` as the public wrapper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  text-generation split.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_text_generation.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_providers_http_exception_passthrough.py tests/unit/services/ai/test_structured_output.py tests/unit/test_model_listing.py -q`
  - Passed: 19 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_text_generation.py`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_text_generation.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-40-57Z-ai-manager-text-generation.md`
  - Passed; backend quick gate passed inside the hook.

## Next Steps

- Continue extracting the remaining image generation loop from
  `ai_service_manager.py`.

## Linked Commits

Pending
