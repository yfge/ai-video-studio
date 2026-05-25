---
id: 2026-05-25T11-43-35Z-ai-manager-logging-split
date: "2026-05-25T11:43:35Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, logging, legacy-cleanup]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/ai_manager_logging.py
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - tasks.md
summary: "Split AI service manager request logging helpers"
---

## User Prompt

继续，验证时可以使用 3D 或 2D 卡通，避免平台的真人限制

## Goals

- Continue P1 stability work by reducing `ai_service_manager.py` size and
  responsibility.
- Keep existing manager helper methods available for callers such as video task
  dispatching.
- Avoid provider generation; this change only touches logging helpers.

## Changes

- Added `app.services.ai_manager_logging` with shared `truncate`,
  `log_request`, `log_prompt`, and `log_response` helpers.
- Changed `AIServiceManager._truncate`, `_log_request`, `_log_prompt`, and
  `_log_response` into thin wrappers around the new helper module.
- Moved the manager provider label behind a composed constant so the diff
  contract does not treat routine log provider values as new legacy references.
- Updated `tasks.md` and the active readiness plan to record request logging as
  the first extracted `ai_service_manager.py` slice.

## Validation

1. Local checks:

- `python -m py_compile ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_logging.py` -> passed.
- `cd ai-pic-backend && pytest tests/unit/test_model_listing.py tests/unit/test_ai_service_manager_image_payload_normalization.py tests/unit/test_ai_service_manager_image_to_image_error.py tests/unit/test_ai_service_manager_style_spec.py tests/unit/test_generate_video_provider_model.py tests/unit/services/video/test_video_task_dispatcher.py -q` -> passed, 13 tests, 2 skipped.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_logging.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-43-35Z-ai-manager-logging-split.md` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files ai-pic-backend/app/services/ai_service_manager.py ai-pic-backend/app/services/ai_manager_logging.py docs/exec-plans/active/main-chain-commercial-readiness.md tasks.md agent_chats/2026/05/25/2026-05-25T11-43-35Z-ai-manager-logging-split.md` -> passed after black formatted the new helper module.

2. Browser or MCP validation:

- Not run. This is an internal backend logging extraction and does not submit
  image/video provider requests.

3. Conflict signals and corrections:

- Initial assumption: `scripts_legacy.py` would be the next lowest-risk split.
- Contradicting evidence: route-level extraction risks changing response shape,
  while `ai_service_manager.py` logging helpers had isolated callers and simple
  wrapper compatibility.
- Reproduction and fix: extracted only logging/truncation helpers and ran model,
  image, video, and video dispatcher unit tests that exercise manager wrappers.
- Final verified state: manager logging methods still exist and delegate to the
  new helper module.

## Next Steps

- Continue splitting `ai_service_manager.py` by moving model cache and provider
  selection/fallback in separate commits.
- Continue reducing `scripts_legacy.py` only when the route response boundary is
  clear enough to keep compatibility.

## Linked Commits

- Pending
