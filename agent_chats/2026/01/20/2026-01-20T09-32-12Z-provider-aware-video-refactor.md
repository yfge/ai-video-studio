---
id: 2026-01-20T09-32-12Z-provider-aware-video-refactor
date: 2026-01-20T09:32:12Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, video, providers, refactor]
related_paths:
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/ai/base.py
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/video.py
  - ai-pic-backend/app/services/providers/google_provider/video_helpers.py
  - ai-pic-backend/app/services/providers/google_provider/video_request.py
  - ai-pic-backend/app/services/providers/google_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/google_provider/video_vertex.py
  - ai-pic-backend/app/services/video/video_generation_service.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/app/services/video/video_upload_utils.py
  - ai-pic-backend/tests/unit/test_google_provider_video.py
  - ai-pic-backend/tests/unit/test_google_provider_video_tasks.py
  - ai-pic-backend/tests/unit/services/video/test_video_generation_service.py
  - docker/.env.example
summary: "Added Vertex-aware Veo video handling with shared request builders and refactored video OSS uploads to meet size limits."
---

## User Prompt
提交现有更改

## Goals
- Commit current provider-aware video generation updates.
- Bring oversized files under size limits with minimal refactor.
- Validate backend tests and required Docker build.
- Run Chrome E2E smoke validation.

## Changes
- Added Google video/Vertex config fields and wired them into provider config/AI base.
- Split Veo request body building and Vertex-specific polling/parsing into dedicated helpers.
- Supported base64 video payloads from Vertex responses and upload to OSS.
- Refactored OSS upload helpers into `video_upload_utils` to keep service files under limits.
- Updated unit tests to cover Vertex responses and new upload helper usage.
- Documented new env vars in `docker/.env.example`.

## Validation
- `cd ai-pic-backend && pytest` (failed: 92 failed, 7 errors; existing suite failures include missing fixtures and integration/env-dependent tests).
- `./docker/build_prod_images.sh` (succeeded; images built and pushed, tag `3d48d92`).
- Chrome MCP E2E: logged in at `http://localhost:8089/login` using `geyunfei` / `Gyf@845261`, redirected to home and saw nav items (e.g., “虚拟IP”).

## Next Steps
- Investigate and resolve pre-existing failing tests/fixtures if required for CI.
- Consider pruning unused OSS helper wrappers if no external callers depend on them.

## Linked Commits
- None (pending commit).
