---
id: 2026-01-27T12-00-45Z-backend-persist-agent-run-task-types
date: 2026-01-27T12:00:45Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, tasks, audit, refactor, p0]
related_paths:
  - ai-pic-backend/app/services/task_agent_run/__init__.py
  - ai-pic-backend/app/services/task_agent_run/builder.py
  - ai-pic-backend/app/services/task_agent_run/builders_assets.py
  - ai-pic-backend/app/services/task_agent_run/builders_narrative.py
  - ai-pic-backend/app/services/task_agent_run/builders_script_ops.py
  - ai-pic-backend/app/services/task_agent_run/builders_text.py
  - ai-pic-backend/app/services/task_agent_run/builders_video.py
  - ai-pic-backend/app/services/task_agent_run/persistence.py
  - ai-pic-backend/app/services/task_agent_run/utils.py
  - ai-pic-backend/app/services/task_agent_run_persistence.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/services/task_worker_assets.py
  - ai-pic-backend/app/services/task_worker_storyboard_media.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence_extra.py
  - tasks.md
summary: "Persisted Task.parameters.agent_run for more task types (dialogue audio/timeline/storyboard/video/text/assets) and refactored the persistence code into a small builder package."
---

## User Prompt

继续完成 P0「任务队列/可审计性补齐」：补齐其它 task_type 的 `agent_run` 落库（dialogue_audio/storyboard/timeline/video…）。

## Goals

- 扩大 `Task.parameters.agent_run` 的覆盖面，确保主要生成/编排链路具备可审计执行轨迹
- 控制文件体积（services ≤250 行），避免继续膨胀
- 增加单测，降低回归风险

## Changes

- 新增 `app/services/task_agent_run/`（builder + persistence），按 kind 构建并写入 `Task.parameters.agent_run`
- 兼容层：保留 `app/services/task_agent_run_persistence.py` 作为 re-export，避免大量改动 import
- Worker/Service 接入：
  - `task_worker.py`：dialogue_audio / timeline_generation / storyboard_generation / timeline_pipeline / text_generation 等任务完成时落库
  - `task_worker_assets.py`：virtual_ip/environment 图像与 variants 任务完成时落库（从 `task_worker.py` 拆出以控制文件体积）
  - `task_worker_storyboard_media.py`：storyboard_images 完成时落库
  - `video_task_polling_service.py`：video_generation 轮询将 parent Task 标记 COMPLETED 时落库
- 新增单测：`tests/unit/services/test_task_agent_run_persistence_extra.py`
- 更新看板：`tasks.md` 将“补齐更多 task_type 的 agent_run 审计”标记为完成

## Validation

- Backend 单测：`pytest -q tests/unit/services/test_task_agent_run_persistence_extra.py`
- 生产镜像构建：`./docker/build_prod_images.sh`
- Chrome E2E（本任务实现过程中已跑通）：
  - 登录 `http://localhost:8089`（账号 `geyunfei`）
  - 调用 `POST /api/v1/scripts/109/storyboard/generate-async` 触发任务（task_id: 5846）
  - 校验 `GET /api/v1/tasks/5846` 返回 `parameters.agent_run`，前端 `/tasks` 详情页展示“Agent 执行轨迹”
  - 备注：首次 task 5845 未展示因 worker 镜像/进程未重启导致代码未生效，重启 `ai-video-celery-worker` 后复测通过

## Next Steps

- 把 `agent_run` 覆盖补齐到失败态/取消态（FAILED/CANCELLED）并记录 error context
- 推进 TaskType 扩展与历史任务回填（含前端 `/tasks` task_type 过滤）

## Linked Commits

- (this commit)
