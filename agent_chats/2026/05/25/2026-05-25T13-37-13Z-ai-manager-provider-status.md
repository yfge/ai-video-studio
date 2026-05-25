## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `ai_service_manager.py` with a low-risk provider
  status/config extraction.
- Preserve public provider status and update behavior.

## Changes

- Added `app.services.ai_manager_provider_status`.
- Moved provider status payload construction and provider config updates out of
  `AIServiceManager`.
- Added focused unit tests for the helper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  split.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_status.py ai-pic-backend/tests/unit/test_ai_manager_provider_status.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_manager_provider_status.py -q`
  - Passed: 2 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_status.py ai-pic-backend/tests/unit/test_ai_manager_provider_status.py`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_provider_status.py ai-pic-backend/tests/unit/test_ai_manager_provider_status.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-37-13Z-ai-manager-provider-status.md`
  - Passed; backend quick gate passed inside the hook.

## Next Steps

- Continue extracting the remaining text and image generation loops from
  `ai_service_manager.py`.

## Linked Commits

Pending
