---
id: 2025-12-13T13-10-03Z-frontend-style-presets-ui
date: 2025-12-13T13:10:03Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, style, image_generation]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/hooks/useStylePresets.ts
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Frontend now fetches style presets from backend and sends style_preset_id in all txt2img/img2img entry points."
---

## User Prompt

后端作为风格唯一真源；前端在不同页面只传部分（至少 preset_id），统一改动全部文生图/图生图结点，并能在 UI 上选择风格预设。

## Goals

- 前端不再硬编码 preset 列表：从后端 `/api/v1/styles/presets` 拉取并复用。
- 在环境/虚拟IP/分镜图像生成入口把 `style_preset_id` 透传到后端（保留 legacy `style` 兼容）。
- 让图生图弹窗与页面表单都能选择 preset，并能复用同一套 hook/cache。

## Changes

- `src/utils/api.ts`
  - 增加 `StyleSpec/StylePreset/StyleSchemaResponse` 类型与 `styleAPI`（schema/presets）。
  - 扩展环境文生图/图生图、虚拟IP文生图/图生图、分镜图片生成请求 payload：支持 `style_preset_id` 与 `style_spec`（可选）。
- `src/hooks/useStylePresets.ts`
  - 新增 presets 拉取 + 内存缓存 hook（避免多处重复请求）。
- `src/components/ImageToImageModal.tsx`
  - 新增「风格预设」下拉框（默认“不使用预设”），提交时带上 `style_preset_id`。
- `src/app/environments/page.tsx`
  - 环境卡片「AI 生成参考图」区域新增 preset 下拉框，并在创建任务时写入 payload。
  - 环境图生图弹窗默认继承当前环境卡片选中的 preset。
- `src/app/virtual-ip/[id]/images/page.tsx`
  - 虚拟IP文生图表单新增 preset 下拉框。
  - 虚拟IP图生图任务提交时带上 `style` + `style_preset_id`。
- `src/app/episodes/[id]/storyboard/page.tsx`
  - 分镜图像生成任务透传 `style_preset_id/style_spec`（来自 ImageToImageModal）。

## Validation

- Frontend lint:
  - `cd ai-pic-frontend && npm run lint`（通过；存在少量既有 unused eslint-disable warning）
- Chrome E2E (localhost:8089):
  - 登录账号 `geyunfei`
  - 打开 `http://localhost:8089/environments`，在「办公室」卡片选择 `cyberpunk_neon` preset
  - 点击「一键生成参考图」创建文生图任务；在 `http://localhost:8089/tasks` 用脚本查询最新任务，确认 `parameters.style_preset_id == "cyberpunk_neon"`
  - 回到环境页点击参考图打开「环境图生图」弹窗，确认弹窗内 preset 默认继承为 `cyberpunk_neon`
  - 提交图生图任务；在任务列表再次脚本查询最新任务，确认 `parameters.style_preset_id == "cyberpunk_neon"`

## Next Steps

- 根据页面语境开始传 `style_spec` 的子集（例如环境页只传背景/光影/色调相关维度）。
- 在虚拟IP/分镜页增加“高级风格”面板（可选）来编辑对应维度子集。

## Linked Commits

- feat(frontend): send style preset id in image requests

