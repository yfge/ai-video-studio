---
id: 2026-05-25T12-22-09Z-ai-manager-image-assets-split
date: "2026-05-25T12:22:09Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, image-assets, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_image_assets.py
  - ai-pic-backend/tests/unit/test_ai_service_manager_image_payload_normalization.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI manager generated image asset normalization"
---

## User Prompt

commit 然后继续

## Goals

- Continue reducing `AIServiceManager` after model resolution extraction.
- Move generated image URL/base64 normalization and OSS upload out of the
  manager.
- Keep the existing manager wrapper so current generation paths and tests do not
  need call-site changes.

## Changes

- Added `app.services.ai_manager_image_assets.convert_base64_images_to_oss`.
- Replaced the body of `AIServiceManager._convert_base64_images_to_oss` with a
  thin wrapper around the helper module.
- Kept existing image generation and image-to-image call sites unchanged.
- Updated `tasks.md` and the active readiness plan to record generated image
  asset normalization as another completed manager split.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 8 tests, 2 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-22-09Z-ai-manager-image-assets-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_image_assets.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T12-22-09Z-ai-manager-image-assets-split.md` -> passed.

2. Browser or MCP validation:

- Not run. This is an internal backend image asset helper extraction and does
  not change a user-visible browser flow or submit provider generation.

3. Conflict signals and corrections:

- The existing wrapper tests already cover dict URL normalization and data URL
  upload metadata through `AIServiceManager._convert_base64_images_to_oss`.
- The extraction leaves the wrapper in place so image generation paths still call
  the same manager method.

## Next Steps

- Continue splitting remaining `AIServiceManager` image reference preload and
  fallback loop mechanics in separate commits.
- Continue reducing `scripts_legacy.py` only where route compatibility can be
  kept explicit.

## Linked Commits

- Pending
