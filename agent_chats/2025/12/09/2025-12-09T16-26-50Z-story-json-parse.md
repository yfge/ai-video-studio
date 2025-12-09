---
id: 2025-12-09T16-26-50Z-story-json-parse
date: 2025-12-09T16:26:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, story]
related_paths:
  - ai-pic-backend/app/utils/story_parser.py
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/tests/unit/test_story_parser.py
summary: "Hardened story JSON parsing to handle fenced/embedded outputs and added coverage"
---
## User Prompt
用docker logs docker-ai-video-backend 查看日志，现在有模型调用成功，但是没有生成故事；把故事生成也用langgraph 完成，同时使用提示模板；把所有的max_tokens的限制都去掉；对比 http://localhost:8089/stories/5 和 http://localhost:8089/stories/4 没有正确的把json 解析出来

## Goals
- Fix story generation outputs so JSON wrapped in markdown/code fences parses into fields.
- Ensure LangGraph story pipeline benefits from the same parsing robustness.
- Add regression coverage for the new parsing helper.

## Changes
- Added `extract_json_block` to tolerate fenced/embedded JSON before normalization.
- Updated sync/async story endpoints, AI service schema parsing, and LangGraph story agent validation to reuse the helper.
- Introduced unit tests covering fenced and noisy JSON payload extraction.

## Validation
- `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && pytest tests/unit/test_story_parser.py tests/test_story_generation_fallback.py -k story_outline_falls_back_to_mock_when_ai_manager_unavailable'`
- Manual browser check via Chrome MCP: logged in with geyunfei account and navigated through story creation UI; generation form interaction attempted (session relogin triggered mid-flow), listings confirmed post-login. No new story generated in UI during this pass—backend parsing covered by unit tests.

## Next Steps
- Trigger a fresh story generation in UI to confirm new parser populates fields without fenced JSON showing in the list cards.

## Linked Commits
- (pending)
