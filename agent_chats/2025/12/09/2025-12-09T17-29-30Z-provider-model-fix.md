---
id: 2025-12-09T17-29-30Z-provider-model-fix
date: 2025-12-09T17:29:30Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-manager]
related_paths:
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/app/services/providers/openai_provider.py
summary: "Fix provider model selection carryover and correct OpenAI JSON schema payload"
---
## User Prompt
生成剧集 LLM 调用有返回，但是前端列表 为空 | 2025-12-10T00:58:26.870+08:00 [INFO] ai-video-studio.com/ai-video-studio b7d20eea966e 172.66.0.243 /api/v1/episodes/generate-async 5fbaee69ac224d0da1c74c1f6faac91e _log_response 439 LLM Response | task=generate_text provider=deepseek model=deepseek-chat status=success usage={'prompt_tokens': 1954, 'completion_tokens': 4097, 'total_tokens': 6051, 'prompt_tokens_details': {'cached_tokens': 0}, 'prompt_cache_hit_tokens': 0, 'prompt_cache_miss_tokens': 1954} body=```json

## Goals
- Stop reusing an invalid model id when falling back across providers so deepseek/openai runs succeed.
- Prefer reliable per-provider defaults when auto-selecting models to avoid bad remote listings.
- Fix OpenAI structured outputs so json_schema requests do not return 400 errors.

## Changes
- Updated AI service manager to choose a provider-specific model each attempt, preferring static provider defaults and avoiding carryover across retries.
- Switched OpenAI json_schema payload to nest `strict` inside the schema object, matching API expectations and preventing 400 responses.

## Validation
- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py`
- Manual API: `POST /api/v1/episodes/generate` (story 7, model deepseek:deepseek-chat, 1 episode) returned a populated episode and stored record `episodes.id=10`.
- Chrome MCP: 登录 geyunfei/Gyf@845261，打开故事 7 页面，剧集概览显示第 1 集及场景预览。

## Next Steps
- Monitor async episode tasks after deploy; if tasks still hang, consider disabling non-working providers (google/volcengine) or shortening provider timeouts.

## Linked Commits
- (pending)
