---
id: 2026-01-14T12-06-17Z-frontend-image-gen-advanced-fields
date: 2026-01-14T12:06:17Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, ui, image-gen]
related_paths:
  - ai-pic-frontend/src/utils/modelUi.ts
  - ai-pic-frontend/src/components/shared/ImageGenAdvancedFields.tsx
  - ai-pic-frontend/src/components/shared/ImageGenAdvancedFieldGrid.tsx
  - ai-pic-frontend/src/components/shared/imageGenAdvancedTypes.ts
  - ai-pic-frontend/src/components/shared/index.ts
summary: "Add shared provider-aware advanced parameter fields for image generation"
---

## User Prompt

优化所有 provider 和域：在选择不同 provider 时动态加载输入以获取额外信息，并按原子化分布提交。

## Goals

- 为文生图 / 图生图提供统一的“高级参数”输入模块（seed/steps/cfg/negative/strength 等）
- 支持按 provider/model 能力动态显示/隐藏对应输入（基于 `metadata.ui.image_gen`）

## Changes

- 新增通用 UI：`ImageGenAdvancedFields` + `ImageGenAdvancedFieldGrid`，用于渲染可选高级参数与 provider notes
- 新增类型：`ImageGenAdvancedValue`，统一高级参数字段形状
- 扩展 `extractImageGenUi()`：从后端 `metadata.ui.image_gen` 解析 supports flags + notes（含版本回退）

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`

## Next Steps

- 将 `ImageGenAdvancedFields` 接入虚拟 IP 文生图 / 图生图入口，并在提交 payload 时透传可选字段
- 将 `ImageGenAdvancedFields` 接入环境生图 / 变体入口，按 provider 动态展示字段

## Linked Commits

- N/A (pending)

