---
id: 2026-07-02T09-59-24Z-canvas-task-deeplink
date: "2026-07-02T09:59:24Z"
participants:
  - human
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - tasks
  - frontend
  - browser-validation
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/components/features/tasks/useTasks.ts
  - ai-pic-frontend/src/components/features/tasks/TasksPage.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksList.tsx
  - ai-pic-frontend/tests/tasksDeepLink.test.tsx
summary: "Open canvas task evidence links on a focused task detail view."
---

## User Prompt

/goal 继续完善无限画布功能

## Goals

- Continue the infinite production canvas with a concrete user-facing increment.
- Make `/tasks?task_id=<id>` links from canvas Task evidence land on the exact task record instead of the generic task list.
- Keep the change inside existing canvas/task page structures.

## Changes

- Updated the `/tasks` route to parse `task_id` on the server and pass it into `TasksPage`.
- Updated `useTasks` to load a single task through the existing `taskAPI.getTask` endpoint when `task_id` is present.
- Added a focused task banner, highlight state, and auto-expanded details for the linked task.
- Added frontend coverage for task-page single-task deep links.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/tasksDeepLink.test.tsx` -> passed, 1 test.
- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings: anonymous default export in `eslint.config.mjs`, and two existing `<img>` warnings in reference image fields.
- `cd ai-pic-frontend && npm run build` -> passed; `/tasks` built as a dynamic route after server-side `task_id` parsing.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/app/tasks/page.tsx ai-pic-frontend/src/components/features/tasks/useTasks.ts ai-pic-frontend/src/components/features/tasks/TasksPage.tsx ai-pic-frontend/src/components/features/tasks/TasksList.tsx ai-pic-frontend/tests/tasksDeepLink.test.tsx` -> passed.
- `pre-commit run --files ai-pic-frontend/src/app/tasks/page.tsx ai-pic-frontend/src/components/features/tasks/useTasks.ts ai-pic-frontend/src/components/features/tasks/TasksPage.tsx ai-pic-frontend/src/components/features/tasks/TasksList.tsx ai-pic-frontend/tests/tasksDeepLink.test.tsx agent_chats/2026/07/02/2026-07-02T09-59-24Z-canvas-task-deeplink.md` -> passed after prettier normalized three frontend files.
- Full `cd ai-pic-frontend && npm run test` was not rerun in this July 10 closure; the known prior failure was the existing long-running `tests/toastProvider.test.tsx` issue, while the focused task deep-link test passed.

2. Browser or MCP validation:

- Entry URL: `http://127.0.0.1:3161/tasks?task_id=77`.
- User path: local Next dev server opened the task deep link, `/api/v1/tasks/77` was deterministically mocked, then the page rendered the linked task.
- Engine: Playwright Chromium fallback. The proof needed deterministic API response mocking for `/api/v1/tasks/77`; fallback recorded explicitly.
- Network: captured request and 200 response for `/api/v1/tasks/77`.
- Result: the page showed `正在查看任务 #77`, highlighted one focused task, auto-expanded `任务ID：77`, and exposed `查看全部任务` linking back to `/tasks`.
- Console: only React DevTools and HMR informational logs were captured during the dev-server proof.
- Evidence: `artifacts/runs/canvas-task-deeplink-20260710T-browser/browser_flow.canvas_task_deeplink.json`, `network.canvas_task_deeplink.json`, `console.canvas_task_deeplink.json`, and `screenshots/tasks_task_id_77.png`.

3. Conflict signals and corrections:

- The first Playwright assertion accidentally matched the sidebar `任务` navigation link when checking the "view all tasks" entry; the assertion was narrowed to require the `查看全部任务` link text and the browser proof was rerun successfully.
- Full frontend test risk remains isolated to the known `toastProvider` long-hang behavior, not to the canvas/task files changed here.

## Next Steps

- Keep the existing `toastProvider` hang as a separate frontend test-health issue.
- If the canvas needs end-to-end proof from node execution through task detail without mocked API, run it against a seeded lite stack with a real generated task.

## Linked Commits

- Pending.
