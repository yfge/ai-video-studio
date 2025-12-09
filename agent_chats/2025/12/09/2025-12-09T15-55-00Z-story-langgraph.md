---
id: 2025-12-09T15-55-00Z-story-langgraph
date: 2025-12-09T15:55:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, story, langgraph]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/story_agent.py
summary: "Add LangGraph story agent, fix async story extra_metadata crash, and verify via UI"
---
## User Prompt
把故事生成也用langgraph 完成， 同时使用提示模板

## Goals
- Run story generation through a LangGraph pipeline using existing prompt templates.
- Fix the async story task failure so generated outlines persist correctly.
- Validate end-to-end in the UI and note task/result behavior.

## Changes
- Added `StoryLangGraphAgent` with a draft+validate graph using the story outline template and JSON schema checks.
- Wired AI service to prefer the LangGraph agent before fallback generation and kept template usage.
- Fixed `extra_metadata` comprehension to avoid dict_items crash in sync/async story creation; deduped exclusion keys.

## Validation
- `pytest tests/test_story_generation_fallback.py`
- Chrome E2E (MCP): login with geyunfei/Gyf@845261, navigate to Stories, create async story “LangGraph 故事验证” with DeepSeek default, saw success toast.

## Next Steps
- Consider running full pytest suite once CI resources allow.
- Monitor task table to ensure `result_file_path` now points to `story:<id>` for async jobs.

## Linked Commits
- 6cad1d0
