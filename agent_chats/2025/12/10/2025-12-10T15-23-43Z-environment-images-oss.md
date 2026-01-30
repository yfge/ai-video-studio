---
id: 2025-12-10T15-23-43Z-environment-images-oss
date: 2025-12-10T15:23:43Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, image, oss]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Persist environment images via shared image persistence helper so they upload to OSS when configured."
---

## User Prompt

- “生成成功了，但是图片没有上传 OSS”

## Goals

- Ensure environment reference images follow the same storage abstraction as virtual IP images: upload to OSS when configured, otherwise store locally.

## Changes

- Updated the `_download_and_attach` helper in `story_structure` environment endpoints to call `ai_service._persist_generated_image` instead of directly downloading to `/uploads`.
- Environment `reference_images` now store the OSS URL when upload succeeds, falling back to the local `/uploads/...` relative path otherwise.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py tests/unit/test_base_provider_client.py -q`
- Manual Docker verification required to confirm new environment image URLs reflect OSS domain.

## Next Steps

- Add an integration test for environment image generation that asserts the returned URLs are OSS-based when `oss_service` is configured.

## Linked Commits

- pending
