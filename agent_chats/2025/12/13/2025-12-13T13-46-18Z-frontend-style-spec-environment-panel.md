---
id: 2025-12-13T13-46-18Z-frontend-style-spec-environment-panel
date: 2025-12-13T13:46:18Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, styles, environments]
related_paths:
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/StyleSpecAdvancedPanel.tsx
  - ai-pic-frontend/src/hooks/useStyleSchema.ts
summary: "Add per-environment advanced StyleSpec panel and send partial style_spec in env image generation requests."
---

## User Prompt
按页面语境开始“只传部分 style_spec”的高级面板（环境/虚拟IP/分镜分别暴露不同维度），并把 style_spec/resolution 信息展示到任务详情/资产详情里（后端已落库，可直接读）。

## Goals
- 环境页支持选择少量 StyleSpec 维度（partial override），只把选择的字段传给后端。
- 图生图弹窗也能传递 `style_spec`（为后续分镜/虚拟IP复用打底）。
- 环境资产页展示已落库的 `style_spec` / `style_spec_resolution`（上次生成信息）。

## Changes
- Added `useStyleSchema` cache hook to fetch `/api/v1/styles/schema` once and reuse.
- Added reusable `StyleSpecAdvancedPanel` component (collapsed by default) that only outputs chosen keys.
- Extended `ImageToImageModal` to collect/submit `style_spec` and optionally render the advanced panel.
- Wired environment txt2img + env img2img modal to send `style_spec` (partial) alongside `style_preset_id`.
- Displayed last env generation `style_spec` + `style_spec_resolution` from `Environment.metadata` in `ai-pic-frontend/src/app/environments/page.tsx`.

## Validation
- `cd ai-pic-frontend && npm run lint`
- Chrome E2E (http://localhost:8089):
  - 登录 `geyunfei` / `Gyf@845261`
  - 进入 `环境资产`，展开某环境的“高级风格”，选择 `color_mood=cinematic_lut` 后点击“一键生成参考图”
  - DevTools 里执行 `fetch('/api/v1/tasks?skip=0&limit=1', {headers:{Authorization:'Bearer '+localStorage.getItem('auth_token')}})` 确认最新任务 `parameters.style_spec.color_mood === 'cinematic_lut'`

## Next Steps
- 虚拟IP图像页（文生图/图生图）接入同一套 advanced panel，并展示落库的 spec/resolution。
- 分镜页（关键帧/首尾帧）接入 advanced panel，并把 spec/resolution 展示在分镜 meta 或任务详情。
- 任务页增加“详情”展开以展示 task.parameters + 关联资产的落库 spec/resolution。

## Linked Commits
- feat(frontend): add env style spec advanced panel

