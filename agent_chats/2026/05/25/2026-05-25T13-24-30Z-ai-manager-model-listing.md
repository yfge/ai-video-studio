## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue the P1 `ai_service_manager.py` decomposition with a small atomic
  helper extraction.
- Keep model listing behavior unchanged while reducing manager size.

## Changes

- Added `app.services.ai_manager_model_listing` for model-list aggregation.
- Moved cache lookup/storage, enabled-provider filtering, remote/static/auto
  source selection, capability-based model type matching, payload construction,
  and stable sorting out of `AIServiceManager.list_models`.
- Kept `AIServiceManager.list_models` as the public compatibility wrapper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  slice.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_listing.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_model_listing.py -q`
  - Passed: 8 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_listing.py`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_model_listing.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-24-30Z-ai-manager-model-listing.md`
  - Passed; backend quick gate passed inside the hook.

## Next Steps

- Continue reducing `ai_service_manager.py`, especially remaining generation
  fallback loops that still live inside the manager.

## Linked Commits

Pending
