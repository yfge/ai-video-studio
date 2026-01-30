---
id: 2025-12-05T16-32-42Z-volc-seedream-image-fix
date: 2025-12-05T16:32:42Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-providers, bugfix]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Treat Seedream 4.5 as an image model and surface it in Virtual IP image selectors"
---

## User Prompt

你再看一下文档 ，如果再胡说我就把你卸载了！！！！！https://www.volcengine.com/docs/82379/1541523?lang=zh

## Goals

- Align Seedream 4.5 integration with the official Volcengine Ark docs, which clearly describe it as an image generation model.
- Make Seedream 4.5 visible and selectable in the Virtual IP image generation model list.

## Changes

- Fixed `VolcengineProvider.available_models` so `seedream-4.5` is registered as `TEXT_TO_IMAGE` with basic image capabilities instead of `TEXT_GENERATION`.
- Updated `virtual_ip_images.get_available_models` to add a `Seedream 4.5` entry under the Volcengine section when Volcengine credentials are configured, and prefer it as the default Volcengine image model.

## Validation

- ai-pic-backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py -q`

## Next Steps

- Once we confirm the exact Seedream 4.5 image API parameters we use in production, add a focused test that calls `/api/v1/ai/generate/image` or `/virtual-ip/{id}/images/generate` with `seedream-4.5` to ensure end-to-end compatibility.

## Linked Commits

- (pending)
