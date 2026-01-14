---
id: 2026-01-14T10-41-23Z-frontend-split-virtualip-image-generation-form
date: 2026-01-14T10:41:23Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, refactor]
related_paths:
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationOptionsFields.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationStyleFields.tsx
summary: "Refactor virtual IP text-to-image form into smaller components to stay under TSX file limits"
---

## User Prompt

优化所有 provider 和域的文生图/图生图提示词规范，并在选择不同 provider 时动态加载输入；要求原子化分布提交。

## Goals

- 将 `ImageGenerationForm.tsx` 拆分到可维护的模块，确保 TSX 文件长度不超标
- 为后续新增 provider-aware 高级参数输入留出空间（不引入功能改动）

## Changes

- 拆分虚拟 IP 文生图表单：
  - 新增 `ImageGenerationStyleFields.tsx`（风格预设 + style spec 面板）
  - 新增 `ImageGenerationOptionsFields.tsx`（类别/张数/补充提示词/默认图）
  - `ImageGenerationForm.tsx` 保留模型/档位/风格/尺寸等核心入口并组合渲染

## Validation

- `cd ai-pic-frontend && npm run lint`（通过；存在既有 warning）
- `./docker/build_prod_images.sh`（成功；IMAGE_TAG=33db115）

## Next Steps

- 在文生图与图生图 UI 中接入后端 `metadata.ui.image_gen`，按 provider/model 动态展示 `seed/steps/cfg_scale/negative_prompt/strength` 等输入

## Linked Commits

- (pending)

