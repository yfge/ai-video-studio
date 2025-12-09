---
id: 2025-12-09T09-56-13Z-streaming-text
date: 2025-12-09T09:56:13Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models, reliability]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/openai_provider.py
  - ai-pic-backend/app/services/providers/deepseek_provider.py
  - ai-pic-backend/app/services/providers/volcengine_provider.py
  - ai-pic-backend/app/services/providers/google_provider.py
  - ai-pic-backend/app/services/providers/minimax_provider.py
summary: "Switch text generation to streaming-first across providers to reduce timeouts, with fallbacks to non-stream requests."
---
## User Prompt
还是超时，都改用流式吧。

## Goals
- Prefer streaming chat completions for text providers to keep long generations alive and reduce timeout failures.
- Keep behaviour backward compatible via fallbacks to non-stream requests.

## Changes
- Added `stream` propagation through `AIServiceManager.generate_text` (default on) so text providers can opt into streaming.
- OpenAI/DeepSeek/Volcengine/Google providers now issue streaming chat requests, aggregate deltas, and fall back to non-stream on errors or empty streams; Google uses `streamGenerateContent` + SSE parsing. Kept structured output handling and error logging.
- Minimax ignores the incoming `stream` flag to avoid sending unsupported params.

## Validation
- `cd ai-pic-backend && pytest tests/test_ai_service.py -q`
- Chrome (http://localhost:8089/): logged in as `geyunfei`, opened 故事创作, filled "流式故事测试" with角色“老拐”，创建异步故事任务 -> success toast observed.

## Next Steps
- Consider provider-specific stream toggles (env or request-level) if any upstream API shows instability.

## Linked Commits
- (this commit)
