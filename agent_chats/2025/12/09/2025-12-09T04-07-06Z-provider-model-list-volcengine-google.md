---
id: 2025-12-09T04-07-06Z-provider-model-list-volcengine-google
date: 2025-12-09T04:07:06Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Hooked Volcengine and Google providers to remote model lists with whitelist filtering and fallbacks"
---
## User Prompt
实现火山和google的模型获取；所有的模型列表都应该用provider 官方model-list api 获取

## Goals
- Use provider official model-list APIs for Volcengine and Google
- Keep whitelist control and safe fallbacks to static lists

## Changes
- Volcengine: call Ark `/models`, intersect with local whitelist, heuristically type remote IDs if whitelist empty, fallback to static list on errors
- Google: call Vertex `/v1/models` with API key, intersect with whitelist, add `x-goog-api-key` header, fallback to static list on errors

## Validation
- Not run (read-path only, no behaviour beyond listing); recommend exercising `/api/v1/ai/models/available` in a running env to confirm credentials and endpoints

## Next Steps
- Provider-specific refinements if actual APIs require different paths/params; monitor logs when the endpoint is exercised

## Linked Commits
- (pending)
