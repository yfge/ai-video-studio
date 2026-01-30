---
id: 2025-12-23T04-08-08Z-google-veo-adapter
date: 2025-12-23T04:08:08Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, google, video]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/providers/google_provider/helpers.py
  - ai-pic-backend/app/services/providers/google_provider/image.py
  - ai-pic-backend/app/services/providers/google_provider/models.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/models_video.py
  - ai-pic-backend/app/services/providers/google_provider/video.py
  - ai-pic-backend/app/services/providers/google_provider/video_helpers.py
  - ai-pic-backend/app/services/providers/polling_utils.py
  - ai-pic-backend/app/services/video/video_generation_service.py
  - ai-pic-backend/app/utils/model_utils.py
  - ai-pic-backend/tests/unit/test_google_provider_image.py
summary: "Aligned Google image/video generation with docs and added Veo models metadata"
---

## User Prompt

Further align Google integrations: multi-reference image-to-image (contents + inlineData), full imageConfig parameters (aspect_ratio/image_size/response_modalities), model list UI metadata, and Veo video calls.

## Goals

- Align Google image generation request shape (contents + inlineData, multi-reference).
- Support imageConfig and responseModalities parameters end-to-end.
- Add Veo video generation and model UI metadata.
- Preserve OSS upload compatibility for video downloads.

## Changes

- Expanded Google image helpers and image generation to handle multiple reference images plus responseModalities/aspectRatio/imageSize.
- Added Veo video implementation and model metadata, including long-running operation polling.
- Updated model resolution and OSS upload handling; adjusted Google image unit test expectations.

## Validation

- `pytest` (ai-pic-backend) — timed out after 120s with multiple existing failures.
- `./docker/build_prod_images.sh` — success.
- MCP/Chrome: opened `http://localhost:8089/`, `http://localhost:8089/environments`, `http://localhost:8089/environments/aab17f172446462a97e738772337d272` → all returned 502 Bad Gateway; unable to run UI flow.

## Next Steps

- Restore the local web app (502) to complete end-to-end UI verification for environment/image/video flows.
- Investigate and address the existing failing pytest suite.

## Linked Commits

- TBD
