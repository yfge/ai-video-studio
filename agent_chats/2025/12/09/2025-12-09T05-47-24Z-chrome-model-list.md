---
id: 2025-12-09T05-47-24Z-chrome-model-list
date: 2025-12-09T05:47:24Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [validation, backend, ai-models]
related_paths:
  - ai-pic-backend/app/api/v1/ai_providers.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/services/providers/base.py
summary: "Chrome MCP validation of remote-first model listing API"
---
## User Prompt
你现在对模型列表 这个 API 进行整体的review和测试 我已经在backend 的.env 中给你列了相应的api key。

## Goals
- Verify the updated model listing endpoint returns remote provider models with authentication.
- Confirm provider coverage and sample entries in browser context.

## Changes
- No code changes; this entry logs MCP browser validation.

## Validation
- Chrome MCP script on `http://localhost:8000/api/v1/ai/models/available` (post login via API) returned 200 with 207 models; providers set: deepseek, google, keling, openai, volcengine; sample includes deepseek-chat, deepseek-reasoner, gemini-3-pro-preview (remote data).

## Next Steps
- Optionally add automated browser test for virtual IP image model selector when fixtures exist.

## Linked Commits
- d0d7a23b2252f2d7d0914596dcf1de33980e0db6
