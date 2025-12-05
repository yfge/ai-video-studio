---
id: 2025-12-05T16-04-26Z-image-text-image-api
date: 2025-12-05T16:04:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-providers, image]
related_paths:
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Unify text-to-image and image-to-image model interfaces and add image-to-image API entrypoint"
---
## User Prompt
对照官方文档 实现 各个文生图以及图生图的模型接口

## Goals
- Provide a unified backend interface for text-to-image and image-to-image across providers.
- Ensure providers that support image-to-image (e.g. OpenAI DALL-E 2, JiMeng) are correctly advertised and routed.

## Changes
- OpenAI provider now declares support for `IMAGE_TO_IMAGE`, and the DALL-E 2 model advertises `image_to_image` capability.
- Added `AIServiceManager.image_to_image` to route image-to-image requests to providers that support `AIModelType.IMAGE_TO_IMAGE`, selecting an appropriate default model.
- Exposed a new `/api/v1/ai/generate/image-to-image` endpoint with `ImageToImageRequest` for unified graph-based image editing/variation.
- Hardened story structure beat creation endpoint to map duplicate order errors to HTTP 400 instead of surfacing raw `ValueError`, keeping validation tests green.

## Validation
- ai-pic-backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py -q`

## Next Steps
- When additional providers expose official image-to-image APIs, mirror their model types (`IMAGE_TO_IMAGE`) and capabilities so they flow through the same manager.
- Optionally add dedicated tests for `/api/v1/ai/generate/image-to-image` once providers are configured in test settings.

## Linked Commits
- (pending)
