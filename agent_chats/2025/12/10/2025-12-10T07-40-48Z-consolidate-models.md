---
id: 2025-12-10T07-40-48Z-consolidate-models
date: 2025-12-10T07:40:48Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, models]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Remove redundant virtual IP model list API and route all img2img model fetches through the unified /ai/models/available."
---

## User Prompt

- “后端现在一共整了几个模型列表的接口？…整体合并成一个。”

## Goals

- Use a single model listing endpoint across the app and drop the virtual-IP-specific variant.

## Changes

- Removed `/virtual-ips/{id}/models/available` handler from `virtual_ip_images.py`; rely solely on `/api/v1/ai/models/available`.
- Updated frontend virtual IP images page to fetch models via unified `aiAPI.getAvailableModels` with `model_type=image`; removed bespoke virtual IP model fetcher in `utils/api.ts`.
- Kept lint clean.

## Validation

- `npm run lint` (frontend).

## Next Steps

- Verify the img2img modal on the virtual IP images page now shows models from the unified endpoint; report any missing providers with the API response.

## Linked Commits

- pending
