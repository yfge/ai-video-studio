---
id: 2025-12-18T14-28-41Z-start-or-end-video
date: 2025-12-18T14:28:41Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, video]
related_paths:
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
summary: "Allow storyboard video generation to use start-only or start+end frames with model-driven UI."
---

## User Prompt

- “生成视频要支持只选首帧或是选择首帧和尾帧。”

## Goals

- 让分镜视频生成在支持尾帧的模型下也能选择仅首帧或首尾帧。
- 保持参数 UI 按模型元数据渲染。

## Changes

- 在 `StoryboardVideoModal` 增加“使用尾帧”开关，尾帧缺失时可关闭，仅用首帧生成；打开时按模型支持和候选尾帧自动填充。
- 生成按钮校验尾帧选择仅在开启尾帧时触发；提交 payload 仅在开启且选择尾帧时传 `end_image_url`。

## Validation

- `npm run lint`
- `./docker/build_prod_images.sh`（tag b8b391b）

## Next Steps

- 填充尾帧候选加载逻辑，避免“暂无候选图”导致频繁手动切换。

## Linked Commits

- (pending)
