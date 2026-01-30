---
id: 2026-01-16T01-43-32Z-virtualip-txt2img-reference-images
date: 2026-01-16T01:43:32Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, image-gen, providers, virtual-ip]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/tests/unit/services/ai/test_images_generation_mixin.py
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPReferenceImagesField.tsx
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/generation.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/image.types.ts
summary: "虚拟IP文生图支持 reference_images：provider-aware 选择器 + 后端透传"
---

## User Prompt

全局检查文生图/图生图提示词规范；确认模板语义与 provider 参数一致性；并按 provider 做进一步优化（动态加载输入，原子化分布提交）。

## Goals

- 让虚拟 IP 文生图也能像环境文生图一样按模型能力展示/提交 `reference_images`
- 后端把 `reference_images` 归一化后透传到支持的 provider（避免“UI 展示了但提交被丢弃”）

## Changes

- Backend: 虚拟 IP 文生图（sync/async）读取并透传 `reference_images`，并在 `ImageGenRequest` 中补齐 `backend_base` 以进行 URL 归一化
- Backend: Celery worker 任务执行时一并传递 `reference_images`
- Backend: 单测覆盖虚拟 IP 文生图 `reference_images` 透传到 AI manager 的调用参数
- Frontend: 虚拟 IP 文生图表单按所选模型动态展示参考图选择器，并随 `/images/generate(-async)` 请求提交 `reference_images`

## Validation

- Backend unit: `cd ai-pic-backend && pytest tests/unit/services/ai/test_images_generation_mixin.py -q`
- Frontend lint: `cd ai-pic-frontend && npm run lint`
- Docker: `./docker/build_prod_images.sh`
- Chrome E2E (MCP):
  - 登录 `geyunfei` 后进入 `http://localhost:8089/virtual-ip/1`
  - 点击「AI 生成图片」→ 在「参考图（可选）」选择 1 张参考图 → 点击「提交生成任务」
  - DevTools Network: `POST /api/v1/virtual-ips/1/images/generate-async` (reqid=259, 200)，请求体包含 `reference_images: [...]`

## Next Steps

- 将 `reference_images` 动态输入扩展到分镜文生图入口，并补齐 provider×domain 兼容矩阵用例

## Linked Commits

- (pending)
