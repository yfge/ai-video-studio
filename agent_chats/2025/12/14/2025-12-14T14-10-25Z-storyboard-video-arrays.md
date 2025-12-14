---
id: 2025-12-14T14-10-25Z-storyboard-video-arrays
date: 2025-12-14T14:10:25Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, storyboard, video]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-backend/tests/unit/test_storyboard_keyframes_schema.py
summary: "Store storyboard video outputs as arrays and surface them in frontend (with prompt override for keyframes)"
---

## User Prompt

生成的视频也要以数组形式保存

## Goals

- 视频生成结果按数组存储（视频、封面、尾帧），避免覆盖历史版本。
- 前端读取数组并优先展示最新一条，兼容旧字段。
- 图像生成支持 prompt 覆盖与首/尾开关（与上一需求联动）。

## Changes

- Schema 增加 `video_urls/video_thumbnail_urls/video_last_frame_urls`，单测覆盖。
- 视频生成任务写入时合并去重视频/封面/尾帧列表，同时保留单值兼容。
- 图像生成请求新增 `prompt/start_enabled/end_enabled`，后端透传到 worker 并按开关生成；支持 prompt 覆盖。
- 前端类型补充视频数组字段，分镜展示逻辑优先使用数组首项；图生图弹窗调用带 prompt 及开关。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_storyboard_keyframes_schema.py`
- `cd ai-pic-frontend && npm run lint`
- Chrome：登录后在 `http://localhost:8089/episodes/10/storyboard` 继续正常加载、可切换场景。

## Next Steps

- 若需要展示多版本视频/封面，可在 UI 增加多源切换；目前取数组首项显示。

## Linked Commits

- feat(storyboard): target start/end keyframes with prompt hint
