---
id: 2026-01-27T13-14-07Z-task-agent-run-failed-cancelled
date: 2026-01-27T13:14:07Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks, audit, migration, p0]
related_paths:
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
  - ai-pic-backend/app/services/task_agent_run/persistence.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
  - ai-pic-backend/alembic/versions/b1b863e84acc_add_task_cancelled_status.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_failed.py
summary: "Extended Task audit so FAILED/CANCELLED tasks also persist parameters.agent_run with error context; added TaskStatus.CANCELLED and a migration."
---

## User Prompt

- 把 FAILED/CANCELLED 任务也写入 `parameters.agent_run`（补 error context，审计闭环）

## Goals

- 任务失败时也能在 `/tasks` 直接看到可审计的执行轨迹与错误信息
- video 任务在“提交阶段失败/轮询阶段失败”两种路径都能落库 agent_run
- 为后续“任务取消”留出状态位（CANCELLED）

## Changes

- Backend: 扩展 `TaskStatus` 增加 `CANCELLED`
- Backend: `persist_task_agent_run` 支持在 `COMPLETED/FAILED/CANCELLED` 任务上写入 `parameters.agent_run`
  - 对失败任务补齐 `task_status` 与 `error.message`
  - 当 builder 无法构建（无 result_ref）时写入最小 fallback（prompt/method/status/error/result_ref from parameters）
- Backend: video 轮询聚合时，父 Task 失败补齐 `error_message`（取子任务首个 error）
- Backend: storyboard video 的 Celery 入口在 finally 中持久化 agent_run（确保提交阶段失败也能落库）
- Migration: Alembic 新增 `taskstatus` enum 值 `CANCELLED`
- Tests: 新增单测覆盖 failed fallback + failed enrich

## Validation

- Backend tests:
  - `cd ai-pic-backend && pytest -q tests/unit/services/test_task_agent_run_persistence_failed.py`
  - `cd ai-pic-backend && pytest -q tests/unit/services/test_task_agent_run_persistence_extra.py`
- Prod images: `./docker/build_prod_images.sh`（tag=e0b2515）
- Chrome E2E (MCP):
  - 登录 `http://localhost:8089/login`（`geyunfei`）
  - 重启 worker：`docker restart ai-video-celery-worker`（确保加载最新代码）
  - 触发一个“提交阶段必失败”的 video 任务：
    - `POST /api/v1/scripts/110/storyboard/generate-video`（script 110 无分镜 frames）→ `task_id=5847`
    - `GET /api/v1/tasks/5847` 返回 `status=failed` 且 `parameters.agent_run.task_status=failed`、`error.message=未找到分镜数据`
    - `/tasks` 页面点开该任务详情，看到 “Agent 执行轨迹” 已展示（method=video_generation）

## Next Steps

- 进一步细分 image 相关 TaskType（storyboard_images / virtual_ip / environment）并同步前端过滤选项
- 若要支持真正取消：补 `/tasks/{id}/cancel` + worker 侧取消检查（并把状态写成 `CANCELLED`）

## Linked Commits

- (this commit)

