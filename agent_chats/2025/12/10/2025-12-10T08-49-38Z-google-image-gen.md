---
id: 2025-12-10T08-49-38Z-google-image-gen
date: 2025-12-10T08:49:38Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, models, google]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/tests/unit/test_google_provider_image.py
summary: "Add Google Gemini text-to-image and image-to-image support and surface it in the unified model list."
---

## User Prompt

- “接入google的图生图和文生图，参考 文档 https://ai.google.dev/gemini-api/docs/image-generation?hl=zh-cn”

## Goals

- Enable Google Gemini text-to-image and image-to-image generation.
- Ensure Google image-capable models appear in `/api/v1/ai/models/available`.

## Changes

- Extended `GoogleProvider` to support `TEXT_TO_IMAGE` and `IMAGE_TO_IMAGE`, implementing `generate_image`/`image_to_image` against the Gemini `generateImage` endpoint with inline reference images.
- Added Gemini 2.0 Flash image model fallback with `image_to_image` capability; broadened capability-aware filtering in the Google provider for remote listings and fallbacks.
- Marked Volcengine Seedream 4.5 with `image_to_image` capability so it surfaces for img2img, and adjusted capability-aware filtering in the service manager.
- Added unit tests for Google image generation stubs and capability-based model listing.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_google_provider_image.py tests/unit/test_model_listing.py -q`
- Chrome MCP (login `geyunfei`/`Gyf@845261`):
  - `/api/v1/ai/models/available?model_type=text_to_image` shows providers `google,keling,openai,volcengine` with `google:gemini-2.0-flash-exp`.
  - `/api/v1/ai/models/available?model_type=image_to_image` shows providers `google,openai,volcengine` with `google:gemini-2.0-flash-exp`.

## Next Steps

- Exercise real Gemini image endpoints with valid keys to confirm payload/response shapes; adjust parsing if Google API changes.
- Wire UI to respect model capabilities when selecting Google image models.

## Linked Commits

- pending
