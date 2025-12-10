---
id: 2025-12-10T12-30-00Z-json-block-shared
date: 2025-12-10T12:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, parsing]
related_paths:
  - ai-pic-backend/app/utils/json_utils.py
  - ai-pic-backend/app/utils/story_parser.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/tests/unit/test_story_parser.py
summary: "Promote extract_json_block to a shared JSON utility and route all AI JSON parsing through it."
---

## User Prompt

- “把story parser 中的extract_json_block 提为公共函数，每个用json的方式都用这个处理一下”

## Goals

- Move the JSON block extraction helper out of `story_parser` into a shared utility.
- Ensure every AI JSON parsing path uses the common extractor instead of ad-hoc `json.loads` or local wrappers.

## Changes

- Introduced `app/utils/json_utils.py` with the shared `extract_json_block`, and re-exported it from `story_parser` for backward compatibility.
- Updated endpoints (`stories`, `episodes`, `scripts`), agents, and `ai_service` to import the shared helper.
- Replaced bespoke `_unwrap_json_block` + `json.loads` flows in script generation/storyboard endpoints with `extract_json_block` fallbacks.
- Extended unit coverage to assert the shared helper and the `story_parser` alias stay in sync.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (no live backend/frontend instance available in this environment).

## Next Steps

- Re-run a Chrome MCP end-to-end path once a live stack is available to confirm AI JSON responses keep parsing correctly.

## Linked Commits

- pending
