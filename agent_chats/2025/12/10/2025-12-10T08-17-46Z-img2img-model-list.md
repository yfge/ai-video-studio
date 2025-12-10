---
id: 2025-12-10T08-17-46Z-img2img-model-list
date: 2025-12-10T08:17:46Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, tests]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/tests/unit/test_model_listing.py
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
summary: "Fix /api/v1/ai/models/available image_to_image filtering and avoid masking 503s as 500s."
---

## User Prompt

- Logs showed `GET /api/v1/ai/models/available?model_type=image_to_image` returning 500 from the backend.

## Goals

- Ensure the unified models endpoint returns the correct image-to-image-capable models.
- Prevent business HTTP errors (e.g., missing providers/models) from being wrapped into 500 responses.
- Keep the virtual IP image page always bound to a valid model once the list loads.

## Changes

- Allowed capability-based inclusion of image-to-image support (e.g., DALL-E 2 variations) when filtering models and avoided premature provider-level filtering.
- Added explicit `image_to_image` capability to Volcengine Seedream 4.5 so it surfaces in img2img model lists.
- Guarded the models endpoint to re-raise `HTTPException` instead of masking 4xx/5xx business errors.
- Added unit coverage for capability-aware filtering and HTTPException passthrough.
- On the virtual IP images page, default to the recommended/first available model once the list loads and block generation until a model is available.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_listing.py -q`
- `cd ai-pic-frontend && npm run lint`
- Chrome MCP: not re-run for this UI fallback (no live backend/frontend instance available in this environment).

## Next Steps

- Monitor other model types for capability-based filtering needs (e.g., image_to_video) and align provider metadata accordingly.
- Re-run Chrome MCP flow once a live stack is available to confirm the guarded model selection UX.

## Linked Commits

- pending
