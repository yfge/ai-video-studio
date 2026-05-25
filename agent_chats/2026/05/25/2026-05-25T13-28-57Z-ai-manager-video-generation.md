## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `ai_service_manager.py` with another isolated helper
  extraction.
- Keep video generation provider selection, model resolution, fallback, logging,
  and terminal error behavior unchanged.

## Changes

- Added `app.services.ai_manager_video_generation`.
- Moved `AIServiceManager.generate_video` fallback orchestration into
  `generate_video_with_fallback`.
- Kept `AIServiceManager.generate_video` as the public wrapper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  video-generation split.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_video_generation.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_generate_video_provider_model.py tests/unit/test_ai_providers_http_exception_passthrough.py -q`
  - Passed: 8 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_video_generation.py`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_video_generation.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-28-57Z-ai-manager-video-generation.md`
  - Passed; backend quick gate passed inside the hook.

## Next Steps

- Continue extracting remaining generation fallback loops from
  `ai_service_manager.py`, with focused tests around each moved path.

## Linked Commits

Pending
