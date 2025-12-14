---
id: 2025-12-14T13-47-40Z-storyboard-scene-selection
date: 2025-12-14T13:47:40Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Stop auto-resetting selected scene; allow manual scene switching in storyboard page"
---

## User Prompt

现在 http://localhost:8089/episodes/10/storyboard 无法选中其他场景

## Goals

- 允许在分镜页面自由切换规范化场景，不被自动回退到首个场景。
- 仍保留首次载入时的默认场景选择（scene_scope/首帧/第一个规范化场景）。

## Changes

- 引入 `sceneSelectionInitialized`，仅在首载入时根据 scene_scope/规范化场景/分镜帧设定默认场景；一旦用户选择场景不再自动重置。
- 场景按钮点击会标记为手动选择，从而避免后续 effect 将场景跳回。

## Validation

- `cd ai-pic-frontend && npm run lint`
- Chrome：登录后在 `http://localhost:8089/episodes/10/storyboard` 点击“场景 10 …”按钮，页面切换到场景 10 的规范化信息与分镜列表（不再自动跳回场景 1）。

## Next Steps

- 如需进一步确认多场景的分镜过滤，可在场景 10 内触发图像/视频生成验证回填。

## Linked Commits

- fix(frontend): keep manual storyboard scene selection
