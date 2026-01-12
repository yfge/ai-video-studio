---
id: 2026-01-12T01-16-58Z-frontend-generation-profile-defaults-display
date: "2026-01-12T01:16:58Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image-gen, generation-profile]
related_paths:
  - ai-pic-frontend/src/components/shared/GenerationProfileSelect.tsx
  - ai-pic-frontend/src/utils/api/types/image-gen.types.ts
summary: "前端统一展示 generation_profile 默认参数，补齐可灵图生图 fidelity defaults"
---

## User Prompt

- 好的，继续下一步。

## Goals

- 前端统一展示 `generation_profile` 的默认参数（不只 steps/cfg/negative/strength，也覆盖可灵图生图的 `image_fidelity/human_fidelity`）。
- 各入口复用同一组件（`GenerationProfileSelect`），避免页面表单散落参数解释。

## Changes

- 扩展 `ImageGenProfileDefaults` 类型：新增 `image_reference`、`image_fidelity`、`human_fidelity`（可选）。
- `GenerationProfileSelect` 默认参数展示补齐：
  - 在“默认参数”一行增加 `ref` / `image_fidelity` / `human_fidelity` 的显示。
  - 根据 `mode` 动态调整 helperText，使图生图场景明确包含 fidelity。

## Validation

- Frontend lint：`cd ai-pic-frontend && npm run lint`
- Chrome E2E（使用账号 `geyunfei`）：
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - 点击任一参考图的“图生图”打开弹窗
  - 选择 provider “可灵”，并切换 profile “身份优先”
  - 观察“默认参数”展示为 `image_fidelity=0.7 · human_fidelity=0.6`（不再显示“（无）”）

## Next Steps

- 继续收敛：把更多 provider 的关键参数也通过 `generation_profile` 统一呈现（例如强度/参考图策略/水印等），并在 UI 上做统一解释。

## Linked Commits

- (pending)
