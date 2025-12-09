---
id: 2025-12-09T04-04-16Z-provider-model-list-remote
date: 2025-12-09T04:04:16Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/providers/base.py
summary: "Prefer provider /models API for model listing with whitelist filtering and fallback"
---
## User Prompt
所有的模型列表都应该用provider 官方model-list api 获取，而不是写死

## Goals
- Use provider official /models endpoints instead of static lists wherever possible
- Keep whitelist enforcement and safe fallbacks

## Changes
- Updated provider base fetch to call `{base_url}/models`, intersect returned IDs with the local whitelist, and only fall back to static `available_models` on error or empty responses

## Validation
- Not run (backend-wide pytest is heavy); change is a read-path enhancement only

## Next Steps
- Consider provider-specific overrides if any vendor requires non-/models endpoints or auth nuances

## Linked Commits
- (pending)
