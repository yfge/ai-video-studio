---
id: 2025-12-18T09-36-57Z-model-metadata-ui
date: 2025-12-18T09:36:57Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, backend, model-metadata, video, image]
related_paths:
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/keling_provider.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Expose per-model UI metadata (size/resolution/duration/flags) from providers and consume it on the frontend; remove seedream-only filters."
---

## User Prompt

前端放开模型筛选，以后端返回为准，同时要注意不同的模型输入参数不同，后端要返回这些参数及选项，让前端动态加载；文生图/图生图同样处理。

## Goals

- Backend: provide per-model UI options (resolution/duration/size/support flags) via the model list API.
- Frontend: stop hardcoding Seedream-only filters; render video and image generation options based on backend metadata.
- Keep aligned with docs and preserve existing flows.

## Changes

- Added `metadata` to `ModelInfo` and wired through AIServiceManager/list_models responses.
- Annotated Keling/Minimax/Volcengine/OpenAI model lists with `metadata.ui` (resolution/duration/ratio/supports_end_frame/camera_fixed/size_options etc.).
- Backend model listing now prefers provider metadata; API returns metadata to the frontend.
- Updated Storyboard video modal to load all image-to-video models, use backend-provided UI options (duration/resolution/ratio, end-frame/camera flags), and drop Seedream-only filters.
- Virtual IP image generation form now uses backend-provided `size_options` for resolution selects; AIModel type now carries metadata.

## Validation

- `pytest tests/unit/test_generate_video_provider_model.py -q`
- `npm run lint` (frontend)
- Chrome MCP: 登录后调用 `GET /api/v1/ai/models/available?model_type=image_to_video`，看到 providers `[keling,minimax,volcengine]`，示例模型 metadata.ui 包含 resolution/duration/end_frame/camera flags。
- `./docker/build_prod_images.sh` (tag a9f6388，前后端镜像构建/推送完成)

## Next Steps

- Extend metadata to other providers as docs become available; add UI rendering for model-specific advanced params if required.
- Re-run Chrome E2E once backend deploys the new metadata to confirm model options populate correctly.

## Linked Commits

- (pending)
