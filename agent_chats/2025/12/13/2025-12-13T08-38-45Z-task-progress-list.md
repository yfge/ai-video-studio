---
id: 2025-12-13T08-38-45Z-task-progress-list
date: 2025-12-13T08:38:45Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, tasks]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
  - ai-pic-backend/app/schemas/task.py
  - ai-pic-backend/tests/test_tasks_minimal.py
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Expose task progress detail, sort tasks by newest ID, and surface progress in the UI."
---

## User Prompt
3. 在任务列表中要可以看到任务的状态（具体执行到哪一步） 这个可以通盘考虑  
4. 任务列表按 ID 倒序

## Goals
- Return per-task progress detail and ID-desc ordering from the API.
- Show progress text in the task list UI with stable ordering.
- Cover the new ordering/progress response shape in automated tests.

## Changes
- Added `progress_detail` to task responses (derived from description/error), ordered task queries by ID desc, and reused progress for async statuses.
- Extended task types in the frontend and rendered the progress row in the task list while sorting client-side for safety.
- Updated task tests to assert the new progress field and descending order.

## Validation
- `pytest ai-pic-backend/tests/api/test_episode_outline_persistence.py ai-pic-backend/tests/test_tasks_minimal.py ai-pic-backend/tests/unit/test_episode_step_outline_light.py`

## Next Steps
- Ensure async generators keep description updated per stage so progress detail remains meaningful.
- Confirm task list displays real-time progress during E2E run.

## Linked Commits
- TODO: add commit hash after commit
