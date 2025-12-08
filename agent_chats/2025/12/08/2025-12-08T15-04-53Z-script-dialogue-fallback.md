---
id: 2025-12-08T15-04-53Z-script-dialogue-fallback
date: 2025-12-08T15:04:53Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/tests/scripts/test_script_story_structure_sync.py
  - ai-pic-backend/tests/scripts/test_script_dialogue_fallback.py
summary: "Add dialogue/stage fallback and ensure normalized scenes sync without empty content, avoiding storyboard blocking."
---

## User Prompt

对白生成不对吧？

## Goals

- Prevent empty/low-quality dialogues from blocking storyboard by adding safe fallbacks when AI output lacks dialogues/stage directions.
- Keep normalized scene sync intact on script generate/regenerate/update.
- Add tests that avoid real LLM calls and validate both scene sync and dialogue fallback.

## Changes

- Added `_populate_dialogues_and_stage_if_missing` to synthesize minimal dialogues/stage directions per scene using story main characters as speakers; wired into script create/generate (sync & async) and regenerate paths.
- Hardened normalized scene sync test to mock AI output and expect one placeholder shot per scene; added new fallback test to ensure dialogues/stage directions are auto-populated and scenes still sync.

## Validation

- `pytest tests/scripts/test_script_story_structure_sync.py tests/scripts/test_script_dialogue_fallback.py`

## Next Steps

- Optionally enrich fallback lines with episode/scene summaries or role metadata and cap duplication when rerunning sync with existing manual edits.
- Consider short-circuiting external LLM calls in dev mode to avoid noisy logs when credentials are absent.

## Linked Commits

- (pending)
