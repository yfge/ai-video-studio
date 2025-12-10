---
id: 2025-12-10T15-40-00Z-model-cache-init
date: 2025-12-10T15:40:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models, caching]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Warm and cache model lists at service init and serve cached models from the available-models API path."
---

## User Prompt

- “先完成这个任务 ，把所有模型列表 在系统进行初始化时做一个缓存 在api/v1/ai/models/available 直接返回缓存”

## Goals

- Preload model lists during service initialization.
- Serve `/api/v1/ai/models/available` from the in-memory cache (auto source) to avoid repeated remote calls.

## Changes

- Added model cache to `AIService`, warming it during initialization via `_warm_model_cache` (pulls per-type lists from `AIServiceManager`).
- `list_models` now returns cached results for auto source (per model type key) and refreshes cache on misses; cache covers all, text, text_to_image, image_to_image, text_to_video, text_to_speech.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change).

## Next Steps

- Consider cache invalidation hooks when provider configs change; add admin refresh endpoint if needed.

## Linked Commits

- pending
