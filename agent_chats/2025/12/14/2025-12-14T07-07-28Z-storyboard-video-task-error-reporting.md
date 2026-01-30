---
id: 2025-12-14T07-07-28Z-storyboard-video-task-error-reporting
date: 2025-12-14T07:07:28Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, celery, storyboard, video, observability]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Stop silent storyboard video successes by returning structured errors from generate_video and failing the Celery task when no videos are produced."
---

## User Prompt

Celery worker 显示 `tasks.storyboard_video_generate ... succeeded ... None`，但没有实际生成视频。

## Goals

- 让“没有生成任何视频”的分镜视频任务明确失败（Task.status=FAILED + error_message），避免误报成功。
- 将根因信息（如 AI manager 未初始化/无可用 provider/模型报错）透传到 task.error_message 和 worker 日志，便于排障。

## Changes

- `AIService.generate_video`：当 `ai_manager` 未初始化或 provider 返回失败时，返回包含 `success=false` 与 `error` 的结构化 dict（不再静默返回 `None`）。
- `_process_storyboard_video_task`：
  - 收集生成结果与错误原因；
  - 若 `generated_count==0` 则抛错并写入 `task.error_message`；
  - 在捕获异常标记 Task 失败后 `raise`，使 Celery 任务也在 worker 日志中表现为失败。

## Validation

- `pytest -q tests/unit/test_generate_video_provider_model.py tests/unit/test_model_listing.py`

## Next Steps

- 线上复验：用同一条分镜点击“生成视频”，应看到 Task 失败原因（例如缺少 `VOLCENGINE_API_KEY` 或 OSS 配置）而不是 Celery 秒回成功。

## Linked Commits

- (pending)
