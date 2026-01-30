---
id: 2025-12-14T07-11-47Z-fix-storyboard-video-anyio-run
date: 2025-12-14T07:11:47Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, celery, storyboard, video, bugfix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Fix storyboard video Celery crash by passing end_image_url as positional arg to anyio.run (no kwargs)."
---

## User Prompt

Celery worker 报错：`TypeError(\"run() got an unexpected keyword argument 'end_image_url'\")`，导致分镜视频任务未执行生成。

## Goals

- 修复分镜视频任务在 Celery worker 中的崩溃，确保能实际调用视频生成逻辑。

## Changes

- `_process_storyboard_video_task`：调整 `anyio.run(...)` 调用方式，不再向 `anyio.run` 传递关键字参数；将 `end_image_url` 改为位置参数传入协程。

## Validation

- `pytest -q tests/unit/test_storyboard_keyframes_schema.py`

## Next Steps

- 重新触发一次分镜视频生成任务，确认不再出现 `anyio.run` 的关键字参数异常，并观察任务是否进入实际视频生成轮询与 OSS 上传流程。

## Linked Commits

- (pending)
