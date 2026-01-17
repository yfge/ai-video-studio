---
id: 2026-01-17T08-37-24Z-frontend-modal-provider-aware
date: 2026-01-17T08:37:24Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, image-gen, provider-aware]
related_paths:
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useReferenceSelection.ts
summary: "Show provider/model notes in ImageToImageModal and enforce single-ref selection when img2img extra images are unsupported."
---

## User Prompt

全局优化文生图/图生图提示词与参数一致性；按 provider 能力进一步优化，并在前端切换不同 provider 时动态展示额外信息（原子化分布提交）。

## Goals

- 在“选择参考图生成关键帧”等图生图弹窗中，始终展示模型/提供商能力提示（即使高级参数折叠）
- 当模型不支持 img2img 多参考图（extra images）时，限制只选择 1 张参考图，并在 UI 明确提示

## Changes

- `ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx`: 新增「模型提示」区块，展示后端下发的 `image_gen` notes；引用选择逻辑抽到 hook 以便按模型能力自适应。
- `ai-pic-frontend/src/components/shared/modals/image-to-image/useReferenceSelection.ts`: 基于 `extractImageGenUi(model, mode)` 推导是否允许多参考图；当不支持时自动裁剪 selection，并把二次选择改为“替换基准参考图”。

## Validation

- `cd ai-pic-frontend && npm run lint`
- Chrome（MCP，Next dev `http://localhost:8090`）：
  - 登录后进入 `http://localhost:8090/episodes/10/storyboard`
  - 点击「选择参考图生成关键帧」打开弹窗，先选择 2 张环境参考图
  - 切换 provider 到 OpenAI（模型 `openai:dall-e-2`）后：参考图自动裁剪为 1 张，并出现「该模型不支持多参考图…」提示
- `./docker/build_prod_images.sh`

## Next Steps

- 文档：补齐 provider×domain 兼容矩阵（reference_images/negative_prompt/extra_images/strength 等）并同步到 tasks.md
- 前端：按 provider/模式动态加载更多输入提示（如 strength/fidelity 可用范围等）

## Linked Commits

- (pending)
