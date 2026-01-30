---
id: 2026-01-15T09-39-05Z-frontend-env-txt2img-reference-picker
date: 2026-01-15T09:39:05Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, story-structure, image-gen]
related_paths:
  - ai-pic-frontend/src/components/features/environments/EnvironmentReferenceImagesField.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/types.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/environments.endpoints.ts
summary: "Add provider-aware reference image picker for environment txt2img"
---

## User Prompt

根据 provider 动态加载输入以得到一些额外的信息，并对所有 provider/域做一致性优化；原子化分布提交。

## Goals

- 在「环境资产 → AI 生成参考图」文生图表单中支持选择已有参考图作为 `reference_images` 输入。
- 仅在所选模型支持 `reference_images` 时展示该输入（避免误导与无效提交）。

## Changes

- 新增 `EnvironmentReferenceImagesField`：从环境图片列表加载可选参考图并支持多选。
- `EnvironmentGenerationFields`：
  - 增加 `envKey` 入参；
  - 使用 `extractImageGenUi(selectedModel, "text_to_image").supportsExtraImages` 动态决定是否展示参考图选择器；
  - 当切换到不支持的模型时自动清空已选 reference_images。
- `EnvironmentSidePanel`：提交环境文生图任务时按需附带 `reference_images`。
- API 类型补齐：`generateEnvironmentImages*` payload 增加 `reference_images?: string[]`。

## Validation

- Frontend lint: `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`
- Chrome (MCP):
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`
  - 在「AI 生成参考图」选择 1 张参考图并点击「创建生成任务」
  - DevTools Network: `POST /api/v1/story-structure/environments/.../images/generate-async` (reqid=914, 200) Request Body 中包含 `reference_images`。

## Next Steps

- 将 reference_images 的 UI/透传扩展到其它需要的 domain（如 storyboard 文生图、虚拟 IP 文生图）并按 provider 能力动态展示。

## Linked Commits

- (pending)
