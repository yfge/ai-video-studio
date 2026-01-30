---
id: 2025-12-13T09-05-39Z-task-progress-episodes
date: 2025-12-13T09:05:39Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, tasks, episode]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
summary: "Improved async episode generation task progress to reflect per-step and per-episode status."
---

## User Prompt

任务 状态不对，现在都是准备调用模型，应该是每一个agent结点，比如生成第几集，校验第几集

## Goals

- Make async episode generation tasks surface granular progress (outline, per-episode generation).
- Keep task descriptions updated during validation and persistence.

## Changes

- Added `_update_task_progress` helper and wired it into the async episode generation worker to report: model call start, outline validation/write, fallback usage, per-episode validation/persistence, and final completion summary.
- Progress detail now updates in-place instead of staying on “准备调用模型”.

## Validation

- Targeted pytest (outline/episode tests) already green in this session: `pytest ai-pic-backend/tests/api/test_episode_outline_persistence.py ai-pic-backend/tests/test_tasks_minimal.py ai-pic-backend/tests/unit/test_episode_step_outline_light.py`.

## Next Steps

- Re-run async generation for story 21 to confirm task progress shows per-episode steps once the gateway 502 is resolved.

## Linked Commits

- TODO: add commit hash after commit
