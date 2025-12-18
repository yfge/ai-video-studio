---
id: 2025-12-18T14-46-31Z-video-endframe-toggle
date: 2025-12-18T14:46:31Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Respect start-only video generation: API toggles tail usage and stops falling back to stored end frames."
---

## User Prompt

- “我在生成视频时并没有传入尾帧，但是视频还是按首尾帧生成的，检查链路是不是直接取了分镜设置的首尾帧，而不是 API 传入的值。”

## Goals

- 允许显式关闭尾帧；当未传尾帧时不要自动回落到分镜里已有的尾帧。

## Changes

- 后端新增 `use_end_frame` 参数（请求/任务参数），处理时若为 False 或 selection 显式传空尾帧，则强制 start-only，不再从分镜数据回落尾帧。
- 前端 API 类型/提交 payload 增加 `use_end_frame`；StoryboardVideoModal 生成视频时传递当前尾帧开关状态。

## Validation

- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts.py ai-pic-frontend/src/components/StoryboardVideoModal.tsx ai-pic-frontend/src/utils/api.ts`（含 backend quick gate/前端 lint）。
- `npm run lint`
- 未重跑 `pytest` 全量；镜像构建待统一重跑。

## Next Steps

- 重跑实际分镜生成：关闭尾帧开关应只用首帧生成；开启时按选择尾帧生成。部署后再验证。

## Linked Commits

- (pending)
