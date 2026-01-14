---
id: 2026-01-14T10-03-52Z-frontend-image-gen-advanced-params
date: 2026-01-14T10:03:52Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, api]
related_paths:
  - ai-pic-frontend/src/utils/api/types/image.types.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/generation.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/virtual-ip-image/variants.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/story-structure/environments.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/storyboard.endpoints.ts
summary: "Align image-gen request parameters (generation_profile, seed/steps/cfg/negative/strength) across domains."
---

## User Prompt
- 全局检查文生图/图生图提示词规范与 provider 参数一致性；根据 provider 进一步优化；选择不同 provider 动态加载输入；原子化分布提交。

## Goals
- 让前端各域（虚拟 IP、环境、分镜）在文生图/图生图请求中统一透传高级参数：`generation_profile`、`seed/steps/cfg_scale/negative_prompt`、`strength`。
- 保持现有调用方式不变（通过 endpoints 模块透传 JSON payload）。

## Changes
- 扩展 `AIImageGenerationRequest` / `ImageToImageRequestPayload` 类型，补齐高级参数字段。
- 虚拟 IP 文生图/图生图（含 variants sync/async）请求体增加 `generation_profile` 与高级参数透传。
- 环境文生图/图生图（含 async）payload 类型补齐高级参数与 `aspect_ratio`。
- 分镜图像生成请求体补齐 `generation_profile` 与高级参数透传。

## Validation
- `cd ai-pic-frontend && npm run lint`（仅 warnings，无 error）。
- `./docker/build_prod_images.sh`（success, IMAGE_TAG=c26373f）。

## Next Steps
- 基于后端 `metadata.ui.image_gen` 在 UI 侧按 provider/model 动态展示/隐藏参数输入，并在 Chrome 做端到端验证（文生图 + 图生图各一条路径）。

## Linked Commits
- (pending)

