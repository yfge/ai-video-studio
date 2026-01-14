---
id: 2026-01-14T14-25-01Z-frontend-txt2img-advanced-params
date: 2026-01-14T14:25:01Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image-gen, providers]
related_paths:
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
  - ai-pic-frontend/src/hooks/virtual-ip/virtualIpImageTypes.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateIcon.tsx
  - ai-pic-frontend/src/components/features/environments/types.ts
  - ai-pic-frontend/src/utils/api.ts
summary: "Expose provider-aware txt2img advanced params across Virtual IP + Environments"
---

## User Prompt
全局检查文生图/图生图提示词与参数规范；按 provider 动态展示额外输入信息；覆盖所有域；原子化分布提交。

## Goals
- 在前端统一暴露文生图（txt2img）的高级参数入口，并确保不同 provider 的能力差异可动态提示/隐藏。
- 确保提交到后端的生成请求 payload 能透传 `negative_prompt` 等关键参数。

## Changes
- Virtual IP 图片页：在文生图表单接入 `ImageGenAdvancedFields`，将 `seed/steps/cfg_scale/negative_prompt` 同步到请求状态。
- 环境资产：在创建/侧边栏生成表单接入 `ImageGenAdvancedFields`，并将高级参数透传到 `/images/generate-async` 请求体。
- API 适配：部分调用切换到拆分后的 `@/utils/api/endpoints`/`@/utils/api/types`；同时在 legacy `src/utils/api.ts` 的 `virtualIPImageAPI` 请求映射中补齐高级参数字段兜底。
- 小型拆分：抽出 `EnvironmentCreateIcon` 以控制页面组件体量。

## Validation
- Dev 访问修复：`docker restart ai-video-nginx`（修复 nginx upstream 缓存旧容器 IP 导致的 `502 Bad Gateway`）。
- Chrome E2E（Virtual IP 文生图）：
  - 登录后进入某个虚拟 IP 的图片管理页 → 点击「AI 生成图片」→ 选择 provider=可灵（`keling:kling-v1`）→ 展开「高级参数」→ 填写 `negative_prompt="no text, watermark"` → 提交。
  - DevTools Network 确认 `POST /api/v1/virtual-ips/1/images/generate-async` 的 Request Body 包含 `negative_prompt` 字段。
- Chrome E2E（环境资产创建并生成参考图）：
  - 进入「环境资产」→「创建环境资产」→ 勾选「创建后自动生成参考图」→ 选择 provider=可灵（`keling:kling-v1`）→ 展开「高级参数」→ 填写 `negative_prompt="no text, watermark"` → 创建。
  - DevTools Network 确认 `POST /api/v1/story-structure/environments/<id>/images/generate-async` 的 Request Body 包含 `negative_prompt` 字段。
- 前端静态检查：`cd ai-pic-frontend && npm run lint`（通过，存在已知 warnings）。
- 生产镜像构建：`./docker/build_prod_images.sh`（通过）。

## Next Steps
- 将同一套高级参数能力扩展到图生图（img2img）链路，并逐域覆盖（如 Virtual IP 图生图、storyboard 等）。
- 基于 provider 能力进一步细化提示词模板/字段说明，形成可复用的“提示词规范 + 参数对齐”文档与 UI 展示策略。

## Linked Commits
- (this commit)

