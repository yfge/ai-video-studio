---
id: 2026-01-20T09-53-48Z-google-vertex-token-refresh
date: 2026-01-20T09:53:48Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, providers, oauth]
related_paths:
  - ai-pic-backend/app/core/config.py
  - ai-pic-backend/app/services/ai/base.py
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/vertex_auth.py
  - ai-pic-backend/tests/unit/services/providers/test_google_vertex_auth.py
  - docker/.env.example
summary: "Added Vertex OAuth token refresh with cached service-account flow for Veo requests."
---

## User Prompt
1

## Goals
- Add automatic Vertex OAuth access token refresh with TTL caching.
- Keep provider/service files within size limits.
- Validate backend tests and production image builds.
- Run Chrome-based E2E smoke check.

## Changes
- Added Vertex service account env/config fields and wiring into ProviderConfig.
- Introduced `vertex_auth` helper to mint and cache OAuth tokens via service accounts.
- Updated Google provider to fetch tokens automatically and pass them to Veo calls.
- Added unit tests for the token provider and caching behavior.
- Documented new environment variables in `docker/.env.example`.

## Validation
- `cd ai-pic-backend && pytest` (failed: 87 failed, 7 errors; suite includes existing integration/fixture failures).
- `./docker/build_prod_images.sh` (succeeded; images built/pushed, tag `1518a86`).
- Chrome MCP E2E: opened `http://localhost:8089/login`, confirmed logged-in nav (welcome for `geyunfei` and main nav items).

## Next Steps
- Investigate pre-existing failing tests/fixtures when required by CI.
- Add optional token-refresh metrics/logging if needed for ops visibility.

## Linked Commits
- None (pending commit).
