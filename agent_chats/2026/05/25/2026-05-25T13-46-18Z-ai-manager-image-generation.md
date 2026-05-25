## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `ai_service_manager.py` by extracting the text-to-image
  generation loop.
- Preserve style spec handling, OpenAI style normalization, provider fallback,
  logging, and successful base64-to-OSS conversion.

## Changes

- Added `app.services.ai_manager_image_generation`.
- Moved `AIServiceManager.generate_image` orchestration into
  `generate_image_with_fallback`.
- Kept `AIServiceManager.generate_image` as the public wrapper.
- Updated `tasks.md` and the active commercial readiness plan with the completed
  image-generation split.

## Validation

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_generation.py`
  - Passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_providers_http_exception_passthrough.py -q`
  - Passed: 6 tests, 2 skipped.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_generation.py`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_generation.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-46-18Z-ai-manager-image-generation.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_generation.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T13-46-18Z-ai-manager-image-generation.md`
  - Passed.

## Next Steps

- Continue extracting the remaining image-to-image loop from
  `ai_service_manager.py`.

## Linked Commits

Pending
