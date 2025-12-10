---
id: 2025-12-10T15-18-46Z-volcengine-handler-retry
date: 2025-12-10T15:18:46Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, image, models]
related_paths:
  - ai-pic-backend/app/services/providers/base.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/tests/unit/test_base_provider_client.py
summary: "Harden Volcengine client reuse by rebuilding closed httpx clients and retrying once when the handler is closed."
---

## User Prompt

- “我他妈的在用火山引擎啊？？？ 你你到底干了什么？”

## Goals

- Stop Volcengine image calls from failing with `handler is closed` errors by rebuilding the httpx client when it has been closed.
- Add regression coverage so `get_client` reinitializes closed clients.

## Changes

- Updated base provider `get_client` to reinitialize when the underlying AsyncClient is closed.
- Added one-shot retry/reinitialize paths in Volcengine text-to-image and image-to-image flows when the handler/connection is closed.
- Added a unit test to ensure closed clients are rebuilt on the next `get_client` call.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_base_provider_client.py tests/unit/test_model_utils.py -q`
- Chrome MCP: not run (backend-only change; service running in Docker separately).

## Next Steps

- Monitor Docker logs to confirm Volcengine calls no longer fail with handler-closed errors; extend retry to other providers if similar errors appear.

## Linked Commits

- pending
