---
id: 2026-06-11T00-10-00Z-task-cancel-endpoint
date: "2026-06-11T00:10:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - tasks
  - api
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/task_control.py
  - ai-pic-backend/app/services/task_control_service.py
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/app/services/script/regeneration_task_helpers.py
  - ai-pic-backend/tests/test_task_cancel_api.py
summary: 新增 POST /tasks/{id}/cancel（best-effort），状态转换表上移到 task model 共享，worker 状态写入加防复活守卫（取消后不被改回 COMPLETED）。
---

# Task Cancel Endpoint

## User Prompt

生产链路优化 Phase B6a：任务无法从 UI 取消，长时间挂起的生成任务只能等超时。

## Goals

- `POST /api/v1/tasks/{task_id}/cancel`：属主校验、按状态机校验（仅 PENDING/PROCESSING 可取消）。
- 状态转换表从超限的 tasks.py（321 行）上移到 `app/models/task.py` 的 `TASK_STATUS_TRANSITIONS` 共享，tasks.py 净行数下降（313 行）。
- 防复活守卫：worker 完成时不得把已取消任务覆盖回 COMPLETED/FAILED。

## Changes

- `app/models/task.py`：新增 `TASK_STATUS_TRANSITIONS`；`tasks.py` 改为 import 引用并删除本地副本。
- 新增 `app/services/task_control_service.py`（走 TaskRepository，无裸 query；404/400 语义）与 `app/api/v1/endpoints/task_control.py`，注册到 api.py。
- `regeneration_task_helpers.update_task_status`：当前状态为 CANCELLED 时跳过写入（script 生成/重新生成路径防复活）。
- 已知限制（记录为后续项）：celery task id 未持久化无法 revoke；script 路径之外的 worker（视频/图片等直接赋值 task.status）取消后仍可能跑完并覆盖状态。
- 新测试 `tests/test_task_cancel_api.py`：5 个用例（pending 取消、processing best-effort、completed 拒绝 400、未知 404、worker 防复活）。

## Validation

- `pytest tests/test_task_cancel_api.py -q`：5 passed。
- `pytest -k task`（排除预存坏模块）：81 passed。

## Next Steps

- B6b：/tasks 列表取消按钮。
- 后续项：其余 worker 状态写入点的 CANCELLED 守卫、celery id 持久化以支持 revoke。

## Linked Commits

- This commit.
