---
id: 2026-01-14T16-34-28Z-environment-img2img-advanced-params
date: 2026-01-14T16:34:28Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, image-gen, environments, img2img, providers]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/tests/unit/services/story_structure/test_environment_image_requests.py
  - ai-pic-frontend/src/components/features/environments/EnvironmentVariantModal.tsx
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/environments.endpoints.ts
summary: "Expose provider-aware img2img advanced params for Environment variants"
---

## User Prompt

全局检查文生图/图生图提示词与参数规范；按 provider 动态展示额外输入信息；覆盖所有域；原子化分布提交。

## Goals

- 环境资产「图生图变体」支持按 provider 动态展示高级参数，并确保参数端到端透传到后端统一归一化逻辑。
- 补齐可灵（keling）图生图关键参数：`image_reference`/`image_fidelity`/`human_fidelity`（以及通用 `seed/steps/cfg_scale/negative_prompt/strength` 在支持的 provider 下可用）。

## Changes

- 后端环境图生图：`resolve_environment_image_variant_request()` / task payload / service 调用补齐 `image_reference`/`image_fidelity`/`human_fidelity`，并透传到 `ImageGenRequest` → `normalize_image_gen_request` → provider-safe 调用。
- 后端 endpoint：`/api/v1/story-structure/environments/{env_id}/images/variants(-async)` 增加 query fallback 参数，JSON body 同样支持上述字段。
- 前端环境图生图弹窗：开启 `ImageToImageModal` 的 `showAdvancedParams`，并在提交 payload 中透传 `seed/steps/cfg_scale/negative_prompt/strength/image_reference/image_fidelity/human_fidelity`。
- 前端 API：`generateEnvironmentImageVariantsAsync` payload 类型补齐上述字段；`EnvironmentVariantModal` 切换到 modular API（`@/utils/api/endpoints`）避免 legacy 类型冲突。
- 测试：新增 resolver/task payload 单测覆盖上述字段。

## Validation

- 后端单测：`cd ai-pic-backend && pytest tests/unit/services/story_structure/test_environment_image_requests.py -q`（通过）。
- 前端静态检查：`cd ai-pic-frontend && npm run lint`（通过，存在已知 warnings）。
- 前端构建：`cd ai-pic-frontend && npm run build`（通过）。
- 生产镜像构建：`./docker/build_prod_images.sh`（通过）。
- Chrome E2E（环境图生图，测试账号 `geyunfei`）：
  - 进入 `http://localhost:8089/environments/aab17f172446462a97e738772337d272` → 在任一环境参考图点击「图生图」→ provider 选择「可灵」→ 展开「高级参数」填写 `image_reference=subject`、`image_fidelity=0.7`、`human_fidelity=0.55` → 提交。
  - DevTools Network 确认 `POST /api/v1/story-structure/environments/<env_id>/images/variants-async` Request Body 包含 `image_reference/image_fidelity/human_fidelity` 字段。

## Next Steps

- 对齐所有 domain 的 txt2img/img2img 参数集合（含 provider notes），并保证 UI 与后端归一化逻辑一致。
- 评估是否需要让 `/api/v1/ai/generate/image-to-image` 也走同一套归一化与参数过滤（避免域间能力漂移）。

## Linked Commits

- (this commit)
