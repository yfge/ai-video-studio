---
id: 2026-05-25T11-01-53Z-step-pipeline-deprecation
date: "2026-05-25T11:01:53Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, api-client, timeline, legacy]
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
  - ai-pic-frontend/tests/scriptApiNamespace.test.ts
  - tasks.md
summary: "Keep deprecated step-by-step pipeline endpoints out of scriptAPI"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “继续”

## Goals

- Keep the timeline pipeline as the default UI API entry.
- Prevent new UI code from reaching the deprecated dialogue-audio,
  audio-timeline, and storyboard-from-audio-timeline steps through `scriptAPI`.
- Preserve named compatibility exports for legacy callers and tests.

## Changes

- Removed the three deprecated step-by-step pipeline functions from the
  `scriptAPI` namespace object.
- Kept the legacy functions as named exports from `script/audio.endpoints.ts`.
- Added a frontend namespace test proving `scriptAPI` exposes
  `generateTimelinePipelineAsync` but not the deprecated step-by-step methods.
- Marked the task-board deprecation convergence item complete.

## Validation

- `cd ai-pic-frontend && npm run test`
  - Result: passed, 21 tests.
- `cd ai-pic-frontend && npm run lint`
  - Result: passed with 18 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run build`
  - Result: passed.
- `python scripts/check_repo_docs.py`
  - Result: passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts ai-pic-frontend/tests/scriptApiNamespace.test.ts tasks.md agent_chats/2026/05/25/2026-05-25T11-01-53Z-step-pipeline-deprecation.md`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- `pre-commit run --files ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts ai-pic-frontend/tests/scriptApiNamespace.test.ts tasks.md agent_chats/2026/05/25/2026-05-25T11-01-53Z-step-pipeline-deprecation.md`
  - Result: passed on rerun after `prettier` formatting, including frontend
    lint.

## Next Steps

- Continue legacy cleanup around `scripts_legacy.py`,
  `dialogue_audio_service.py`, and `ai_service_manager.py`.

## Linked Commits

- Pending
