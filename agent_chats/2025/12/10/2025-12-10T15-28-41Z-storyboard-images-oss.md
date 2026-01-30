---
id: 2025-12-10T15-28-41Z-storyboard-images-oss
date: 2025-12-10T15:28:41Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, image, storyboard, oss]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Route storyboard frame image generation through the shared image persistence helper so generated frames upload to OSS when configured."
---

## User Prompt

- “全局查找是不是有漏掉的环节，不要嘴硬！ 不要嘴硬！！ IP 的文生图，图生图，环境的文生图，图生图，分镜的图生图”

## Goals

- Ensure storyboard (shot/分镜) image generation uses the same OSS-aware persistence path as virtual IP and environment images.
- Avoid leaving storyboard frames pointing at ephemeral provider URLs when OSS is configured.

## Changes

- Updated `_process_storyboard_image_task` in `scripts` endpoints to:
  - Generate images as before via `ai_service.ai_manager.generate_image` / `image_to_image`.
  - For each frame result, call `ai_service._persist_generated_image` to download + upload (with `require_upload=bool(oss_service)`).
  - Store the final OSS URL (or local relative path) back into `frame['image_url']`, while preserving the original provider URL in `frame['image_url_original']`.
- Wired in `oss_service` import so the helper can enforce upload when configured.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py tests/unit/test_base_provider_client.py -q`
- Attempted storyboard tests; some fail due to external Google model 401 and a missing legacy test file, unrelated to this change.

## Next Steps

- Add a focused test that mocks `ai_service._persist_generated_image` and asserts storyboard frames receive persisted URLs rather than provider URLs.

## Linked Commits

- pending
