---
id: 2025-12-09T05-46-07Z-model-list-api-refresh
date: 2025-12-09T05:46:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, ai-models]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/services/providers/base.py
summary: "Make model listing APIs remote-first and drop hardcoded image model lists"
---

## User Prompt

你现在对模型列表 这个 API 进行整体的review和测试 我已经在backend 的.env 中给你列了相应的api key。

## Goals

- Ensure the model listing API uses remote/official model lists instead of static defaults.
- Remove hardcoded image model lists from virtual IP image models endpoint.
- Validate the updated API using configured provider API keys.

## Changes

- Switched `/api/v1/ai/models/available` default source to `auto` and normalized invalid source values to auto.
- Rewrote `virtual_ip_images.get_available_models` to call `ai_service.list_models` (image, auto) and return aggregated provider-prefixed model ids, count, and provider stats; removed legacy hardcoded lists.
- Cleaned up provider base (reverted unused cache addition) to keep behavior unchanged otherwise.

## Validation

- `pytest tests/test_ai_service.py -q`
- Manual API call (auth via `geyunfei` login) to `GET http://localhost:8000/api/v1/ai/models/available` with default source confirmed 200 OK, success true, 207 models across providers: deepseek, google, keling, openai, volcengine (sample includes remote OpenAI/Gemini/DeepSeek ids).

## Next Steps

- Optionally add a virtual IP image models API test when fixture data is available.
- Consider caching remote model lists per provider to reduce latency if needed.

## Linked Commits

- (this commit)
