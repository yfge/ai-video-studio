---
id: 2026-05-25T10-37-22Z-ai-model-cache-warmup
date: "2026-05-25T10:37:22Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, tests, legacy]
related_paths:
  - ai-pic-backend/app/services/ai/models.py
  - ai-pic-backend/tests/unit/test_model_listing.py
  - tasks.md
summary: "Avoid model-cache warmup inside running event loops"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “继续”

## Goals

- Close the task-board warning about `asyncio.run() cannot be called from a
running event loop` during AI service initialization.
- Avoid creating or leaking un-awaited model-cache warmup coroutines in async
  request/test contexts.
- Keep model listing behavior lazy when warmup is skipped.

## Changes

- Updated `_warm_model_cache` to detect an already running event loop before
  calling `asyncio.run`.
- In async contexts, model-cache warmup now exits early and leaves the existing
  lazy `list_models` path responsible for cache population.
- Added a focused async unit test proving warmup does not run inside an active
  event loop.
- Marked the task-board AI initialization warning item complete.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_listing.py::test_warm_model_cache_skips_inside_running_event_loop tests/test_story_generation_fallback.py -q -W error::RuntimeWarning`
  - Result: passed, 2 tests. The previous un-awaited coroutine RuntimeWarning
    did not recur.
- `python -m py_compile ai-pic-backend/app/services/ai/models.py ai-pic-backend/tests/unit/test_model_listing.py`
  - Result: passed.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai/models.py ai-pic-backend/tests/unit/test_model_listing.py tasks.md agent_chats/2026/05/25/2026-05-25T10-37-22Z-ai-model-cache-warmup.md`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `pre-commit run --files ai-pic-backend/app/services/ai/models.py ai-pic-backend/tests/unit/test_model_listing.py tasks.md agent_chats/2026/05/25/2026-05-25T10-37-22Z-ai-model-cache-warmup.md`
  - Result: passed, including backend quick gate.

## Next Steps

- Continue legacy cleanup around `scripts_legacy.py`,
  `dialogue_audio_service.py`, and `ai_service_manager.py`.

## Linked Commits

- Pending
