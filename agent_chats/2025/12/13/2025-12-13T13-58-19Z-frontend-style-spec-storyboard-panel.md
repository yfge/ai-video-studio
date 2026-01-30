---
id: 2025-12-13T13-58-19Z-frontend-style-spec-storyboard-panel
date: 2025-12-13T13:58:19Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, styles, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Enable storyboard image modals to send partial style_spec and surface persisted style_spec/style_spec_resolution in storyboard meta."
---

## User Prompt

按页面语境开始“只传部分 style_spec”的高级面板（环境/虚拟IP/分镜分别暴露不同维度），并把 style_spec/resolution 信息展示到任务详情/资产详情里（后端已落库，可直接读）。

## Goals

- 分镜页图像生成（关键帧/首尾帧）支持 partial `style_spec`（只传选中的维度）。
- 分镜页展示 storyboard meta 中落库的 `image_generation_style_spec` / `image_generation_style_spec_resolution`。

## Changes

- Added storyboard-context `styleSpecFields` (镜头/构图/光影/色彩/情绪) to both storyboard image generation modals.
- Rendered a collapsible “上次图像生成风格信息” section using `storyboard.meta.image_generation_style_*` fields.

## Validation

- `cd ai-pic-frontend && npm run lint`
- Chrome E2E (http://localhost:8089):
  - 登录 `geyunfei` / `Gyf@845261`
  - 打开 `http://localhost:8089/episodes/11/storyboard` → 点击“选择参考图生成关键帧”
  - 在弹窗中展开“高级风格”，选择 `color_mood=cinematic_lut` → 提交任务
  - DevTools 执行 `fetch('/api/v1/tasks?skip=0&limit=1', {headers:{Authorization:'Bearer '+localStorage.getItem('auth_token')}})` 确认最新任务 `parameters.style_spec.color_mood === 'cinematic_lut'`

## Next Steps

- 任务页增加“详情”展开，展示 task.parameters + 关联资产落库 spec/resolution（env/vip/script）。

## Linked Commits

- feat(frontend): add storyboard style spec panel
