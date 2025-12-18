---
id: 2025-12-18T08-56-37Z-keling-image2video-routing
date: 2025-12-18T08:56:37Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, keling, video-generation]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Normalize Keling base URL and accept image_to_video aliases so AIService routes requests correctly."
---

## User Prompt

图生视频接入可灵的 API，现在可灵 API 已经配置好了，并且低层的 API 已经实现了。

## Goals

- Ensure Keling image-to-video API is reachable through AIService/AIServiceManager.
- Align base URL with official endpoint to avoid double /v1.
- Map AIServiceManager image_url/end_image_url parameters into the Keling provider call.

## Changes

- Normalized Keling base URL to strip trailing `/v1` and default to `https://api-beijing.klingai.com`.
- Updated AIService provider config to use the official Keling base host.
- Allowed Keling provider generate_video to accept `image_url`/`end_image_url` aliases and reuse them for `image`/`image_tail`.

## Validation

- `pytest tests/unit/test_generate_video_provider_model.py -q` (passes; warnings only).
- Manual provider construction to verify base URL normalization after adding PyJWT runtime dependency.
- Chrome MCP: login at `http://localhost:8089/login` with `geyunfei` / `Gyf@845261`, landed on homepage with 虚拟IP/环境资产/任务导航可见 (UI loads post-login).
- Ran `./docker/build_prod_images.sh` (backend/frontend images built and pushed with tag `c875b98`).

## Next Steps

- Consider adding dedicated tests for Keling image-to-video payload mapping and task polling.
- Verify end-to-end image-to-video flow in Chrome UI once backend is deployed with updated config.

## Linked Commits

- (pending)
