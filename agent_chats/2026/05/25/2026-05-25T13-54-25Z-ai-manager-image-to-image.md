## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue the P1 stability cleanup by extracting the remaining
  `AIServiceManager.image_to_image` orchestration.
- Preserve provider pinning, reference preload, style spec metadata, OSS
  conversion, terminal failure semantics, and text-to-image fallback behavior.

## Changes

- Added `app.services.ai_manager_image_to_image`.
- Moved image-to-image provider fallback, reference preload coordination,
  success image OSS conversion, and fallback-to-text-to-image orchestration out
  of `ai_service_manager.py`.
- Kept `AIServiceManager.image_to_image` as the public compatibility wrapper.
- Marked the `ai_service_manager.py` split task complete in `tasks.md`.
- Updated the active commercial readiness plan with the extracted
  image-to-image helper.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_to_image.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_ai_manager_image_assets.py tests/unit/test_ai_manager_image_fallback.py tests/unit/test_ai_manager_image_style.py tests/unit/test_ai_manager_model_resolution.py -q`
  - Passed: 15 tests, 1 skipped.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_to_image.py`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_to_image.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-54-25Z-ai-manager-image-to-image.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_to_image.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-54-25Z-ai-manager-image-to-image.md`
  - Passed.

## Next Steps

- Continue P1 cleanup on `dialogue_audio_service.py` or `scripts_legacy.py`.
- Keep P2 sample proof pending until the remaining legacy risk is reduced.

## Linked Commits

Pending
