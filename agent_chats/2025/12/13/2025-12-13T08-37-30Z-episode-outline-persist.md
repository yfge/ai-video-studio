---
id: 2025-12-13T08-37-30Z-episode-outline-persist
date: 2025-12-13T08:37:30Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, episode]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/tests/api/test_episode_outline_persistence.py
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
summary: "Persist validated episode step outlines into story metadata and surface them on the story page."
---

## User Prompt
1. 生成的剧集大纲要进行校验，校验通过以后也写到故事信息中，并在页面上进行展示 ，这一步在大纲校验通过以后就进行写库  
2. 每一集生成以后校验通过就进行写库

## Goals
- Validate episode step outlines and store them immediately with the story for later display.
- Ensure per-episode validation before persisting to the database.
- Show the validated outlines on the story detail page for operators.

## Changes
- Added strict outline parsing in `episodes.py` to validate loglines, persist outline snapshots into `story.extra_metadata`, and reuse them when writing beats.
- Guarded per-episode persistence with schema and data checks, plus a new async flow that shares the same outline/beat handling.
- Added API test covering outline persistence + beat storage, and rendered the outline list (logline + beats preview) on the story detail page.

## Validation
- `pytest ai-pic-backend/tests/api/test_episode_outline_persistence.py ai-pic-backend/tests/test_tasks_minimal.py ai-pic-backend/tests/unit/test_episode_step_outline_light.py`

## Next Steps
- Run a Chrome E2E (story→episode generation) to confirm outlines render in UI and beats are written.
- Re-run broader pytest suite when external services are available to catch env-dependent regressions.

## Linked Commits
- TODO: add commit hash after commit
