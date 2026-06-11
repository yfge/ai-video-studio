---
id: 2026-06-11T00-40-00Z-task-cancel-buttons
date: "2026-06-11T00:40:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - tasks
related_paths:
  - ai-pic-frontend/src/utils/api/endpoints/task.endpoints.ts
  - ai-pic-frontend/src/components/features/tasks/useTasks.ts
  - ai-pic-frontend/src/components/features/tasks/TasksList.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksPage.tsx
summary: /tasks 列表为 pending/processing 任务提供「取消」按钮（modal 确认 → POST /tasks/{id}/cancel → 列表刷新），并补 cancelled 状态的中文标签。
---

# Task Cancel Buttons

## User Prompt

生产链路优化 Phase B6b：B6a 后端取消端点就绪后，前端任务列表提供取消入口。

## Goals

- pending/processing 任务行显示「取消」按钮，确认走 showAlert+onConfirm modal（破坏性操作的正确 modal 用法）。
- 取消成功后静默刷新列表；失败显示错误。
- 状态标签补「已取消」（原 cancelled 显示「未知」）。

## Changes

- `task.endpoints.ts`：`taskAPI.cancelTask(id)`。
- `useTasks.ts`：`cancelTask` action + `cancellingTaskId` state。
- `TasksList.tsx`：取消按钮（按钮内 loading 文案「取消中...」）+ `getStatusText` 增加 cancelled→已取消。
- `TasksPage.tsx`：`handleCancel` 确认弹窗与错误处理。

## Validation

- `npm run test` 71 passed；lint 0 errors；build 通过（B6b 改动包含在最终 build 校验中）。
- 真实浏览器（dev 栈 :8089）：插入 pending 任务 #6043 → 列表显示「取消」按钮 → 确认弹窗 → 确认后行状态变「已取消」、进度显示「已被用户取消」。证据：`artifacts/runs/phase-b-fixes-20260611T052400Z/task_cancelled_in_list.png`。

## Next Steps

- 全系列收尾：`BUILD_PUSH=false ./docker/build_prod_images.sh` + 总结。
- 后续项（B6a ledger 已记）：非 script worker 的 CANCELLED 守卫、celery id 持久化支持 revoke。

## Linked Commits

- This commit.
