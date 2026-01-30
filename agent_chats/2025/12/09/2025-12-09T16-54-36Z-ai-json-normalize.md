---
id: 2025-12-09T16-54-36Z-ai-json-normalize
date: 2025-12-09T16:54:36Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, parsing]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/script_agent.py
summary: "Normalized AI JSON parsing across episodes/scripts/storyboards to handle fenced outputs"
---

## User Prompt

生成剧集也有类似 的```json的问题，整体处理，同时，对于所有的 AI 生成文字 的部分都进行统一的归一化处理

## Goals

- Strip code fences/extra text from AI JSON outputs for episodes, scripts, and storyboards.
- Ensure episode endpoints and agents consume normalized JSON without crashing on ```json blocks.
- Keep test coverage green after the parsing changes.

## Changes

- Adopted `extract_json_block` in episode generation paths: LangGraph agent, AI manager call, and all episode endpoints (sync/regenerate/async) now use normalized payloads and fallback parsing.
- Updated script LangGraph agent and AI manager script fallback to parse fenced JSON and return normalized content.
- Hardened storyboard generation/parsing to extract JSON blocks and return normalized data for downstream use.

## Validation

- `docker exec ai-video-backend bash -lc 'cd /app/ai-pic-backend && pytest tests/unit/test_story_parser.py tests/test_story_generation_fallback.py -k story_outline_falls_back_to_mock_when_ai_manager_unavailable'`

## Next Steps

- Consider adding similar normalization for any remaining AI text pipelines if new models are introduced; otherwise monitor live episode/storyboard runs.

## Linked Commits

- (pending)
