---
id: 2026-01-20T00-39-12Z-backend-video-dispatcher-errors
date: 2026-01-20T00:39:12Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, video, celery, debugging]
related_paths:
  - ai-pic-backend/app/services/video/video_task_dispatcher.py
  - ai-pic-backend/tests/unit/services/video/test_video_task_dispatcher.py
summary: "Preserve provider-specific error details when video task submission falls back"
---

## User Prompt

全局检查文生图/图生图提示词规范；并按 provider 优化输入；以及修复分镜视频生成失败时错误信息太泛的问题，便于定位（例如 Veo 报错被“所有提供商都失败了”吞掉）。

## Goals

- 保留每个 provider 的真实失败原因，汇总到任务失败信息里
- 在任务管理页能直接看到可行动的错误线索（HTTP code / model not found 等）

## Changes

- `VideoTaskDispatcher._submit_with_fallback` 汇总每次尝试的 `provider: error`，在最终失败时追加到 `所有视频生成提供商都失败了: ...`
- 新增单测覆盖「最终错误包含 provider + 详细原因」与「fallback 关闭时不聚合」

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 重启 `ai-video-celery-worker` 后，在 `http://localhost:8089/tasks` 触发一次 `google:does-not-exist` 的分镜视频任务，页面显示 `所有视频生成提供商都失败了: google: ... HTTP 404 ... models/does-not-exist ...`

## Next Steps

- 在 UI 侧把错误信息做分段/折叠展示，避免过长影响可读性
- 对 “时间轴未生成” 的剧集全流程进行排查并补齐生成入口

## Linked Commits

- fix(backend): preserve provider errors in video dispatcher
