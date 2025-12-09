---
id: 2025-12-09T09-58-31Z-openai-jsonobject-guard
date: 2025-12-09T09:58:31Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/providers/openai_provider.py
summary: "Avoid unsupported response_format on OpenAI stream fallback"
---
## User Prompt
OpenAI stream failed with `response_format` json_object unsupported.

## Goals
- Prevent OpenAI streaming/non-stream requests from sending `response_format` when the model does not support it.

## Changes
- Added `_supports_json_object` helper and gate `response_format` usage: json_schema only when structured outputs supported; json_object only for known-compatible models; otherwise drop the field to avoid 400s during streaming and fallback.

## Validation
- `cd ai-pic-backend && pytest tests/test_ai_service.py -q`

## Next Steps
- If more models surface with/without json_object support, extend the compatibility list.

## Linked Commits
- (this commit)
