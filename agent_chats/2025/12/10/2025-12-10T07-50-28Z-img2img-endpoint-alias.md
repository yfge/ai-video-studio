---
id: 2025-12-10T07-50-28Z-img2img-endpoint-alias
date: 2025-12-10T07:50:28Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, models]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Fix img2img model fetching by using the unified endpoint with proper type aliasing for image_to_image."
---

## User Prompt

- “图生图 modal 调用 virtualIPImageAPI.getAvailableModels is not a function；/ai/models/available?model_type=image_to_image 没有区分，全部返回。”

## Goals

- Use the single unified models endpoint for virtual IP img2img modal.
- Support `model_type=image_to_image` filtering on the backend.

## Changes

- Added `image_to_image`/`img2img` aliases in `ai_service.list_models`, mapping to `AIModelType.IMAGE_TO_IMAGE` for proper filtering.
- Virtual IP images page now fetches models via `aiAPI.getAvailableModels({ type: image_to_image })` and no longer calls the removed virtual-IP-specific endpoint.

## Validation

- `npm run lint` (frontend).

## Next Steps

- Reopen虚拟 IP 图生图弹窗确认模型列表正常显示并被过滤；若仍混入非图生图模型，请提供 `/api/v1/ai/models/available?model_type=image_to_image` 响应片段。

## Linked Commits

- pending
