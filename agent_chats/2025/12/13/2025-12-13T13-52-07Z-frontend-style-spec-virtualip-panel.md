---
id: 2025-12-13T13-52-07Z-frontend-style-spec-virtualip-panel
date: 2025-12-13T13:52:07Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, styles, virtualip]
related_paths:
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Add a per-page advanced StyleSpec panel for VirtualIP image generation and display persisted style_spec/style_spec_resolution."
---

## User Prompt
按页面语境开始“只传部分 style_spec”的高级面板（环境/虚拟IP/分镜分别暴露不同维度），并把 style_spec/resolution 信息展示到任务详情/资产详情里（后端已落库，可直接读）。

## Goals
- 虚拟IP图像页：文生图表单支持 partial `style_spec`（只传选择的维度）。
- 虚拟IP图生图：弹窗也能传递 `style_spec`（与 preset 一起提交）。
- 资产详情：在图像卡片中展示落库的 `generation_params.style_spec` / `style_spec_resolution`。

## Changes
- Added VirtualIP-context `StyleSpec` fields (人物比例/五官/线稿/上色/光影/色彩等) to the AI generation form.
- Ensure async txt2img request omits empty `style_spec` and only sends selected keys.
- Wired img2img `ImageToImageModal` on the page to include the same `styleSpecFields` + default spec.
- Displayed `generation_params.style_preset_id` / `style_spec` / `style_spec_resolution` on each image card (collapsible “风格详情”).

## Validation
- `cd ai-pic-frontend && npm run lint`
- Chrome E2E (http://localhost:8089):
  - 登录 `geyunfei` / `Gyf@845261`
  - 打开 `http://localhost:8089/virtual-ip/7/images` → 点击“🤖 AI生成图像” → 展开“高级风格”
  - 选择 `character_proportion=realistic_7_head` → 提交生成任务
  - DevTools 执行 `fetch('/api/v1/tasks?skip=0&limit=1', {headers:{Authorization:'Bearer '+localStorage.getItem('auth_token')}})` 确认最新任务 `parameters.style_spec.character_proportion === 'realistic_7_head'`

## Next Steps
- 分镜页（关键帧/首尾帧）接入同一套 advanced panel，并展示脚本 storyboard meta 的 spec/resolution。
- 任务页增加“详情”展开，展示 task.parameters + 关联资产落库 spec/resolution（含 resolution meta）。

## Linked Commits
- feat(frontend): add virtualip style spec panel

