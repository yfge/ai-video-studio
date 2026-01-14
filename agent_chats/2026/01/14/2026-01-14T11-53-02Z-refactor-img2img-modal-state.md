---
id: 2026-01-14T11-53-02Z-refactor-img2img-modal-state
date: 2026-01-14T11:53:02Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, refactor]
related_paths:
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageStyleFields.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useImageToImageModalState.ts
summary: "Split img2img modal into smaller modules to stay under TSX limits"
---

## User Prompt

继续推进 provider-aware 图生图表单优化，并按原子提交落地改动。

## Goals

- 将 `ImageToImageModal` / `ImageToImageSettingsForm` 拆分到 ≤250 行，避免继续堆积状态导致超限
- 为后续按 provider 动态加载高级参数输入留出空间

## Changes

- 抽出 `useImageToImageModalState` 管理 modal 内部状态与模型加载回调
- 抽出 `ImageToImageStyleFields` 负责风格预设选择与 StyleSpec 面板渲染
- 精简 `ImageToImageModal` / `ImageToImageSettingsForm` 只保留编排与调用

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`

## Next Steps

- 在 img2img modal 内接入基于 `metadata.ui.image_gen` 的高级参数动态输入（seed/steps/cfg/strength 等）
- 同步虚拟 IP / 环境等入口的参数透传与显示

## Linked Commits

- N/A (pending)
