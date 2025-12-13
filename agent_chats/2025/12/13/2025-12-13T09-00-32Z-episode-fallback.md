---
id: 2025-12-13T09-00-32Z-episode-fallback
date: 2025-12-13T09:00:32Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episode]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/tests/api/test_episode_outline_persistence.py
summary: "Added outline-based fallback so episodes persist even when LLM returns non-JSON content."
---

## User Prompt
剧集生成以后没有按集定写入，你看ai-video-celery-worker 已经第 11 集了，但是 http://localhost:3001/stories/21 看不到任何剧集，同时 剧集规划 列表也看不到

## Goals
- Ensure episodes are persisted per-episode even when the model returns unparseable content.
- Keep validated step outlines stored with the story for UI display.
- Cover the fallback path with automated tests.

## Changes
- Added `_build_stub_episodes_from_outlines` and wired it into sync/async generation so logline-based stubs are saved when JSON parse fails, while still recording outlines and agent run info.
- Adjusted async worker to reuse the same outline persistence and progress detail updates.
- Added an API test covering the fallback path when the model returns non-JSON content.

## Validation
- `pytest ai-pic-backend/tests/api/test_episode_outline_persistence.py ai-pic-backend/tests/test_tasks_minimal.py ai-pic-backend/tests/unit/test_episode_step_outline_light.py`

## Next Steps
- Re-run async generation for story 21 and confirm episodes/loglines appear; monitor celery logs for remaining parsing errors.
- Consider forcing non-streaming JSON schema calls for providers that ignore streaming schema.

## Linked Commits
- TODO: add commit hash after commit
