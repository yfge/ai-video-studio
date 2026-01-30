---
id: 2025-12-17T11-08-21Z-frame-value-from-frames
date: 2025-12-17T11:08:21Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Use current storyboard frame count to fill the locked frame input when timeline exists; generation uses that value."
---

## User Prompt

每场景分镜数 10 … 当前场景预计帧数 10（按 timeline beats）， 当前分镜帧数 5 目前还是这样 我认为每场景分镜数 应该为 5 了吧？

## Goals

- Show the actual scene frame count in the disabled input when timeline exists, instead of only the beat count.
- Keep generation aligned with the displayed value.

## Changes

- `framesPerSceneValue` now prefers the current scene's storyboard frame count when timeline is present; falls back to beat count or manual value when empty.
- Scene generation uses `framesPerSceneValue` when timeline exists, ensuring prompt uses the displayed count.

## Validation

- `npm run lint` (frontend) — pass.

## Next Steps

- After同步时间轴并生成占位，确认输入值随帧数量更新；若 beats 与帧数不一致，考虑后端自动补齐以避免偏差。

## Linked Commits

- (pending)
