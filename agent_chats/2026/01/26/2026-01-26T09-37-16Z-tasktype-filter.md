---
id: 2026-01-26T09-37-16Z-tasktype-filter
date: 2026-01-26T09:37:16Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, tasks]
related_paths:
  - tasks.md
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/alembic/versions/c9d8e7f6a5b4_extend_tasktype_enum.py
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/stories/novel.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/regenerate.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/test_tasks_minimal.py
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/components/features/tasks/TaskDetails.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksList.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksPage.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksPagination.tsx
  - ai-pic-frontend/src/components/features/tasks/TasksToolbar.tsx
  - ai-pic-frontend/src/components/features/tasks/taskTypeOptions.ts
  - ai-pic-frontend/src/components/features/tasks/useTaskPersistedStyle.ts
  - ai-pic-frontend/src/components/features/tasks/useTasks.ts
  - ai-pic-frontend/src/components/features/tasks/utils.ts
summary: "Expand backend TaskType and add /tasks task_type filtering"
---

## User Prompt

- 检查并更新 `tasks.md`（对照现有项目真实情况）。
- 任务体系补全：扩展后端 `TaskType`（story/episode/script/dialogue_audio/storyboard/video…）+ 把现有生成入口的 `task_type="image_generation"` 改成正确类型，并给前端 `/tasks` 加 `task_type` 过滤。

## Goals

- 让 Task 记录能区分 story/episode/script/dialogue_audio/timeline/storyboard/video 等域。
- 修复 async 生成入口的错误 `task_type` 赋值。
- 前端 `/tasks` 支持按 `task_type` 过滤，便于定位问题与审计。

## Changes

- Backend
  - 扩展 `TaskType`，新增 story/episode/script/dialogue_audio/timeline/storyboard/video/text 等类型。
  - 新增 Alembic migration 扩展 `tasktype` enum。
  - 将 Story/Episode/Script 相关 async 入口的 task 创建从兜底 `image_generation` 改为对应 `TaskType.*`。
  - 为 `/api/v1/tasks` 增加了 `task_type` 过滤的最小化测试覆盖。
- Frontend
  - `/tasks` 增加类型下拉过滤，并将参数透传到 `taskAPI.getTasks({ task_type })`。
  - 将原 `src/app/tasks/page.tsx` 拆为 feature module（page 仅做 wrapper），避免继续膨胀。
- Docs/Board
  - 更新 `tasks.md`：补充“超大文件拆分”进度，并标记 TaskType/filter 已完成。

## Validation

- Backend: `cd ai-pic-backend && pytest tests/test_tasks_minimal.py` (3 passed)
- Frontend: `cd ai-pic-frontend && npm run lint` (0 errors)
- Prod images: `./docker/build_prod_images.sh` (ok; IMAGE_TAG=360e65a)
- Chrome (MCP):
  - 访问 `http://localhost:8089/login`，使用 `geyunfei` 登录
  - 进入 `http://localhost:8089/tasks`
  - 通过 API 创建 `story_generation` / `script_generation` 两条 Task
  - 使用“类型”下拉选择“剧本生成”，列表仅剩 `script_generation` 任务；切回“全部类型”后恢复

## Next Steps

- Backfill：为历史 Task（title/description 与 type 不一致）提供一次性纠偏脚本或迁移策略。
- Frontend：任务详情把 `parameters.agent_run`（provider/model/usage/reasoning）做结构化展示。
- Backend：把 story/episode/script 的 `/generate-async` 从 `BackgroundTasks` 统一迁移到 Celery worker。

## Linked Commits

- (pending)
