---
id: 2026-01-20T10-17-06Z-vertex-api-key-support
date: 2026-01-20T10:17:06Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, providers, oauth]
related_paths:
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/ai/base.py
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/video.py
  - ai-pic-backend/app/services/providers/google_provider/video_tasks.py
  - ai-pic-backend/app/services/providers/google_provider/video_vertex.py
  - ai-pic-backend/tests/unit/test_google_provider_video_tasks.py
  - docker/.env.example
summary: "Added separate Vertex API key support and headers for Veo requests with updated configuration wiring."
---

## User Prompt

vertext api key 是单独的

## Goals

- Add a separate Vertex API key configuration and use it for Veo requests.
- Allow Google provider init when only Vertex auth is present.
- Validate backend tests, production build, and Chrome E2E.

## Changes

- Added `GOOGLE_VERTEX_API_KEY` config/normalization and ProviderConfig wiring.
- Enabled Google provider initialization when Vertex auth is available without Gemini API key.
- Added Vertex API key headers for Veo submit/poll calls, and updated polling helper.
- Added unit test coverage for Vertex API key header usage.
- Documented the new env var in `docker/.env.example`.

## Validation

- `cd ai-pic-backend && pytest` (failed: 86 failed, 934 passed, 1 skipped, 7 errors; existing suite failures in integration/fixture-dependent tests).
- `./docker/build_prod_images.sh` (succeeded; images built/pushed, tag `a711164`).
- Chrome MCP E2E: opened `http://localhost:8089/`, verified logged-in nav and welcome for `geyunfei`.

## Next Steps

- Decide whether Vertex API key should also be used for non-video endpoints.
- Address pre-existing failing tests if required for CI.

## Linked Commits

- None (pending commit).
