---
id: 2025-12-05T16-16-47Z-volc-seedream-integration
date: 2025-12-05T16:16:47Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-providers]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Align Volcengine provider with Ark Seedream 4.5 docs and expose model in unified registry"
---

## User Prompt

接入https://www.volcengine.com/docs/82379/1541523?lang=zh

## Goals

- Wire Volcengine Ark Seedream 4.5 text model into the unified AI provider layer in a way that matches the official docs.

## Changes

- Added a `seedream-4.5` entry to `VolcengineProvider.available_models` so it appears in `/api/v1/ai/models/available` with proper text-generation capabilities.
- Stopped overriding Volcengine base_url from the manager, allowing the provider to use its Ark default `https://ark.cn-beijing.volces.com/api/v3` as per docs, while keeping API keys sourced from `VOLCENGINE_API_KEY`/`VOLCENGINE_SECRET_KEY`.

## Validation

- ai-pic-backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py -q`

## Next Steps

- Add focused tests for Volcengine text generation once credentials are available in the test environment, and optionally surface Seedream 4.5 as a selectable model in front-end model pickers.

## Linked Commits

- (pending)
