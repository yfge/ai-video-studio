---
id: 2025-12-07T14-05-26Z-mock-script-scenes
date: 2025-12-07T14:05:26Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Improve mock script fallback to reuse episode scenes so summaries aren’t empty"
---
## User Prompt
继续 ，同时注意，你现在的场景内容也是空的

## Goals
- Ensure mock script fallback uses existing episode scenes so scene summaries show up instead of blank placeholders.

## Changes
- Mock script generator now prefers `episode.scenes` (location/time/summary) before plot points and copies those into scenes/dialogues/stage directions.
- Keeps summaries, locations, and timings aligned with generated episodes.

## Validation
- Not run (backend logic only). Will show up on next script regeneration when AI providers fail.

## Next Steps
- Regenerate scripts in UI; scene summaries should now reflect episode scenes even in mock fallback.

## Linked Commits
- pending
