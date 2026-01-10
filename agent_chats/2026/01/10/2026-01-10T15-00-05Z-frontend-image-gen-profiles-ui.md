---
id: 2026-01-10T15-00-05Z-frontend-image-gen-profiles-ui
date: "2026-01-10T15:00:05Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, image-gen, quality, ui]
related_paths:
  - ai-pic-frontend/src/hooks/useImageGenProfiles.ts
  - ai-pic-frontend/src/components/shared/GenerationProfileSelect.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageReferencePicker.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImagePreviewOverlay.tsx
  - ai-pic-frontend/src/components/shared/modals/image-to-image/ImageToImageSettingsForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageGeneration.ts
  - ai-pic-frontend/src/hooks/virtual-ip/useVirtualIPImageVariants.ts
  - ai-pic-frontend/src/components/features/environments/types.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentVariantModal.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/types/image.types.ts
  - ai-pic-frontend/src/utils/api/types/image-gen.types.ts
  - ai-pic-frontend/src/utils/api/types/index.ts
  - ai-pic-frontend/src/utils/api/endpoints/image-gen.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/index.ts
  - tasks.md
summary: "前端引入 generation_profile（质量档位）选择，并贯通图像生成/图生图请求。"
---

## User Prompt

在后端引入“生成参数 preset / profile”（按 provider+model 给默认 steps/cfg_scale/negative_prompt），并让前端统一选择与展示（不再散落在各页面表单）。

## Goals

- 为图像生成引入可控的“质量档位”（generation_profile），提升不同入口的质量一致性
- 前端统一选择/展示 profile，并将字段贯通到虚拟IP/环境/分镜图生图等链路

## Changes

- 新增 profiles API/types/hook：`GET /api/v1/image-gen/profiles` 的前端调用与缓存（`ai-pic-frontend/src/hooks/useImageGenProfiles.ts` 等）
- 新增统一 Profile 选择组件：`ai-pic-frontend/src/components/shared/GenerationProfileSelect.tsx`
- 虚拟IP 文生图：`ImageGenerationForm` 增加 profile 选择并透传到 `/virtual-ips/{id}/images/generate-async`
- 图生图弹窗：重构 `ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx`（拆分子组件）并加入 profile 选择；虚拟IP/环境/分镜相关 onSubmit 均透传 `generation_profile`
- API 层：更新 `ai-pic-frontend/src/utils/api.ts` 的相关请求体/类型，补齐 `generation_profile` 字段
- 任务板：`tasks.md` 标记前端 profile 统一项完成

## Validation

- `npm run lint`（通过，存在少量 warning）
- Chrome (MCP) E2E：
  - 登录 `geyunfei` / `Gyf@845261`
  - 虚拟IP详情页 → 图片管理 → AI 生成图片：选择 `keling:kling-image-v1` 后 profile 自动选中 `balanced`，提交生成；确认请求 `POST /api/v1/virtual-ips/1/images/generate-async` Body 包含 `generation_profile:"balanced"`（task_id=551）
  - 同页任一图片点“图生图”：选择 `keling:kling-image-v1` 后 profile 自动选中 `balanced`，提交图生图；确认请求 `POST /api/v1/virtual-ips/1/images/<image_id>/variants-async` Body 包含 `generation_profile:"balanced"`（task_id=552）
- `pre-commit run`：passed
- `./docker/build_prod_images.sh`：首次执行时 `next build` 因 `ImageToImageModal` 类型报错失败，已修复；将于提交后再跑一次以使用 commit tag 推镜像

## Next Steps

- 将 `generation_profile` 纳入更多入口的默认策略（例如分镜批量生成按钮等无表单入口），并考虑“按模型记忆上次选择”
- 后端继续扩展支持 profiles 的 provider/model（Seedream/OpenAI 等），并在 profiles 文案中体现差异（fast/balanced/quality）

## Linked Commits

- (pending)
