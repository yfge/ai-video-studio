---
id: 2026-06-10T14-40-00Z-timeline-clip-tasks-endpoint
date: "2026-06-10T14:40:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - backend
  - timeline
  - api
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/timeline_clip_tasks.py
  - ai-pic-backend/app/services/timeline_clip_task_status_service.py
  - ai-pic-backend/app/repositories/task_repository.py
  - ai-pic-backend/app/schemas/timeline_clip_tasks.py
  - ai-pic-backend/tests/test_timeline_clip_tasks_api.py
summary: 新增 GET /timelines/{id}/clip-tasks：按 target_business_id 列出当前用户 pending/processing 生成任务并解析 parameters 中的 clip_id，为渲染就绪面板的「生成中」标记提供数据。
---

# Timeline Clip Tasks Endpoint

## User Prompt

生产链路优化 Phase B4a：渲染就绪检查不感知正在生成中的视频任务，需要后端提供"timeline 下 in-flight 任务（含 clip_id）"列表。clip→任务映射已存在于 Task.parameters JSON 与 target_business_id，无需 schema 变更。

## Goals

- `GET /api/v1/timelines/{timeline_id}/clip-tasks`：鉴权（timeline get_accessible + story_owner_filter）、仅当前用户、仅 PENDING/PROCESSING。
- 解析 Task.parameters JSON 的 clip_id（坏 JSON 容错为 null）。
- timelines.py 已 319 行接近限制，端点放独立模块（沿用 timeline_keyframes 模式）。

## Changes

- `TaskRepository.list_active_for_target(user_id, target_business_id)`（repository 层 query，倒序）。
- 新增 `app/schemas/timeline_clip_tasks.py`（Item/ListResponse）。
- 新增 `app/services/timeline_clip_task_status_service.py`（404 校验 + parameters 解析）。
- 新增 `app/api/v1/endpoints/timeline_clip_tasks.py` 并在 `api.py` 注册。
- 新测试 `tests/test_timeline_clip_tasks_api.py`：active 过滤/clip_id 解析/坏 JSON 容错/其他 target 排除/未知 timeline 404。

## Validation

- `pytest tests/test_timeline_clip_tasks_api.py -q`：2 passed。
- `pytest -k timeline`（排除预存坏模块）：220 passed；唯一失败 `test_timeline_shot_plan_silent_clips` 经 git stash 验证在 HEAD 即失败（预存漂移，与本改动无关）。

## Next Steps

- B4b：前端渲染就绪显示「生成中」。
- 跟进（独立问题）：`test_timeline_shot_plan_silent_clips` 预存失败需单独修复。

## Linked Commits

- This commit.
