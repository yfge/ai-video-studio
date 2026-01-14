---
id: 2026-01-14T15-59-32Z-virtualip-img2img-advanced-params
date: 2026-01-14T15:59:32Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, image-gen, virtual-ip, img2img, providers]
related_paths:
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts
  - ai-pic-frontend/src/components/shared/modals/image-to-image/useImageToImageModalState.ts
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageVariants.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/variants.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/image.types.ts
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_requests.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/tests/unit/services/virtual_ip/test_image_variant_requests.py
summary: "Expose provider-aware img2img advanced params for Virtual IP variants"
---

## User Prompt
全局检查文生图/图生图提示词与参数规范；按 provider 动态展示额外输入信息；覆盖所有域；原子化分布提交。

## Goals
- 虚拟 IP「图生图变体」支持按 provider 动态展示高级参数，并确保参数端到端透传到后端统一归一化逻辑。
- 补齐可灵（keling）图生图关键参数：`image_reference`/`image_fidelity`/`human_fidelity`（以及通用 `seed/steps/cfg_scale/strength` 在支持的 provider 下可用）。

## Changes
- 前端 `ImageToImageModal`：新增可选 `showAdvancedParams`，在图生图弹窗内接入 `ImageGenAdvancedFields`（mode=`image_to_image`），并把高级参数合并进 `onSubmit` payload。
- 前端 Virtual IP：在 `VirtualIPImageManager` 开启 `showAdvancedParams`；`useVirtualIPImageVariants` 透传高级参数到 `/variants-async`，并切换到 modular API（`@/utils/api/endpoints`）避免 legacy 类型限制。
- 后端 Virtual IP：`resolve_virtual_ip_variant_request()` / task payload / service 调用补齐 `image_reference`/`image_fidelity`/`human_fidelity`，并透传到 `ImageGenRequest` → `normalize_image_gen_request` → provider-safe 调用。
- 测试：新增 resolver/task payload 单测覆盖上述字段。

## Validation
- 后端单测：`cd ai-pic-backend && pytest tests/unit/services/virtual_ip/test_image_variant_requests.py -q`（通过）。
- 前端静态检查：`cd ai-pic-frontend && npm run lint`（通过，存在已知 warnings）。
- 前端构建：`cd ai-pic-frontend && npm run build`（通过）。
- 生产镜像构建：`./docker/build_prod_images.sh`（通过）。
- Chrome E2E（虚拟 IP 图生图，测试账号 `geyunfei`）：
  - 进入 `http://localhost:8089/virtual-ip/1` → 在图片列表点击任一图片「图生图」→ provider 选择「可灵」→ 展开「高级参数」填写 `image_reference=subject`、`image_fidelity=0.7`、`human_fidelity=0.55` → 提交。
  - DevTools Network 确认 `POST /api/v1/virtual-ips/1/images/<image_id>/variants-async` Request Body 包含 `image_reference/image_fidelity/human_fidelity` 字段。

## Next Steps
- 将同一套 img2img 高级参数能力扩展到「环境资产图生图」与「分镜图生图」等域，并保持 UI/后端参数一致性。
- 评估是否需要让 `/api/v1/ai/generate/image-to-image` 也走同一套归一化与参数过滤（避免域间能力漂移）。

## Linked Commits
- (this commit)

