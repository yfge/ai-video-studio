---
id: 2026-05-25T10-42-20Z-story-fallback-semantics
date: "2026-05-25T10:42:20Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, ai-service, tests, legacy]
related_paths:
  - ai-pic-backend/app/services/ai/story_outline.py
  - ai-pic-backend/tests/test_story_generation_fallback.py
  - tasks.md
summary: "Lock story outline fallback generation-method semantics"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “继续”

## Goals

- Close the task-board item for story fallback test drift.
- Make `ai_fallback` mean a valid normalized fallback payload.
- Make `ai_fallback_invalid` mean fallback text was returned but schema
  validation failed.

## Changes

- Added a named story outline fallback generation-method helper and used it in
  the fallback result assembly path.
- Reworked the fallback tests to use a small mixin probe instead of constructing
  the full `AIService`.
- Added coverage for valid fallback, invalid fallback, and the generation-method
  naming helper.
- Marked the task-board story fallback drift item complete.

## Validation

- `cd ai-pic-backend && pytest tests/test_story_generation_fallback.py -q`
  - Result: passed, 5 tests.
- `python -m py_compile ai-pic-backend/app/services/ai/story_outline.py ai-pic-backend/tests/test_story_generation_fallback.py`
  - Result: passed.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/ai/story_outline.py ai-pic-backend/tests/test_story_generation_fallback.py tasks.md agent_chats/2026/05/25/2026-05-25T10-42-20Z-story-fallback-semantics.md`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `pre-commit run --files ai-pic-backend/app/services/ai/story_outline.py ai-pic-backend/tests/test_story_generation_fallback.py tasks.md agent_chats/2026/05/25/2026-05-25T10-42-20Z-story-fallback-semantics.md`
  - Result: passed on rerun after `isort` import cleanup, including backend
    quick gate.

## Next Steps

- Continue legacy cleanup around `scripts_legacy.py`,
  `dialogue_audio_service.py`, and `ai_service_manager.py`.

## Linked Commits

- Pending
