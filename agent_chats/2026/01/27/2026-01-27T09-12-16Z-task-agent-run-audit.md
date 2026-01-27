---
id: 2026-01-27T09-12-16Z-task-agent-run-audit
date: 2026-01-27T09:12:16Z
participants: [human, codex]
models: [gpt-5.2]
tags: [tasks, backend, frontend, audit]
related_paths:
  - ai-pic-backend/app/services/task_agent_run_persistence.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py
  - ai-pic-frontend/src/components/features/tasks/TaskDetails.tsx
  - tasks.md
summary: "Persisted Task.parameters.agent_run and rendered key fields in /tasks details"
---

## User Prompt

- “P0：任务队列/可审计性补齐”：把 LangGraph/生成链路的 agent 运行轨迹落到 Task.parameters.agent_run，并在前端 /tasks 详情展示；同时对照项目真实情况更新 tasks.md。

## Goals

- 后端：Story/Episode/Script（含 regenerate）任务完成后，将目标实体的 `extra_metadata.agent_run` 关键字段回写到 `Task.parameters.agent_run`（含 prompt/usage/reasoning/result_ref）。
- 前端：/tasks 详情以结构化方式展示 `parameters.agent_run` 的 provider/model/usage/reasoning/prompt。
- 文档：更新 `tasks.md` 反映当前完成度。

## Changes

- Backend: 新增 `app/services/task_agent_run_persistence.py`，在 Celery task 执行完成后将审计信息写入 `Task.parameters.agent_run`。
- Backend: 拆出 `app/services/task_worker_storyboard_media.py`（storyboard image/video tasks），使 `task_worker.py` 回到 ≤250 行并保持 legacy import 兼容。
- Backend: 在 `task_worker.py` 的 story/episode/script 相关 Celery tasks 完成后调用 `persist_task_agent_run(...)`。
- Backend: 移除多个 async 生成入口中未使用的 `BackgroundTasks` 注入参数（避免误导）。
- Frontend: `TaskDetails` 增加 “Agent 执行轨迹” 区块，展示 provider/model/method，并可展开 usage/reasoning/prompt。
- Tests: 新增单元测试 `tests/unit/services/test_task_agent_run_persistence.py` 覆盖 story/episode/script 三类落库行为。
- Tasks board: 更新 `tasks.md` 的 “任务队列与 Agent 执行落库” 状态与下一步。

## Validation

- Backend: `pytest -q tests/unit/services/test_task_agent_run_persistence.py`（3 passed）。
- Frontend: `npm run lint`（0 errors；存在 eslint warnings，未阻断）。
- Chrome E2E:
  - 通过 `POST /api/v1/stories/generate-async` 创建 story task（task_id=5844），等待 Celery 完成。
  - 打开 `http://localhost:8089/tasks` → 点击该任务 “详情” → 确认出现 “Agent 执行轨迹”，显示 `provider=deepseek` / `model=deepseek-chat` / `method=langgraph_story`，并可展开 usage JSON。
- Build: `./docker/build_prod_images.sh` 构建并推送 backend/frontend prod 镜像成功（tag=e8a35eb）。

## Next Steps

- 补齐 Story/Episode/Script/图像任务的集成测试（任务创建 → handler 执行 → Task/目标实体写入校验）。
- 在 `TESTING_GUIDE.md` 补充 Celery 本地运行/调试与任务链路验证路径。
- 生产环境按批次执行一次历史任务 `TaskType` 回填（先 `--dry-run`）。

## Linked Commits

- TBD

