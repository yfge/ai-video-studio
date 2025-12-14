---
id: 2025-12-14T11-51-14Z-storyboard-keyframe-gallery-defaults
date: 2025-12-14T11:51:14Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Default首/尾帧生成发送多张，保证生成时回填 start/end 图集"
---

## User Prompt

图帧和尾帧都应该是图集的，怎么现在只有一个了？

## Goals

- 让首/尾帧生成默认产出图集（多张），而非单张。
- 确保前端所有首/尾帧生成调用都带上大于1的 count。
- 保持现有 start/end 候选回填与展示逻辑不变。

## Changes

- API 客户端在 `keyframe_mode=start_end` 且未显式给出 count 时默认发送 4 张，并在客户端侧做 1~4 的归一化。
- 场景批量首/尾帧生成默认传 `count=4`。
- 两个首/尾帧图生图弹窗的默认生成张数从 1 提升到 4，便于直接得到首/尾帧图集。

## Validation

- `cd ai-pic-frontend && npm run lint`（通过）
- Chrome 自测：使用 `geyunfei / Gyf@845261` 登录后访问 `http://localhost:8089/episodes/10/storyboard`，页面加载正常。

## Next Steps

- 需要多张首/尾帧的分镜重新触发生成以拿到新的图集候选；如需节省算力，可在弹窗内手动调低 count。

## Linked Commits

- fix(frontend): default start/end keyframes to multi-image generation
