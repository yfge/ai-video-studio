---
id: 2026-06-03T11-16-18Z-episode-helper-reexport
date: "2026-06-03T11:16:18Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, episode-generation, import]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/__init__.py
summary: "Keep episode async task re-export lazy after async task refactor"
---

## User Prompt

commit

## Goals

- Fix the episode package import surface discovered while validating the remaining backend changes.
- Keep the compatibility surface narrow and avoid touching unrelated grid/storyboard or script-generation changes.

## Changes

- Kept `app.api.v1.endpoints.episodes.process_episode_generation_task` available as a compatibility re-export.
- Made the re-export lazy so importing the episodes package does not eagerly load the async task service.

## Validation

- `cd ai-pic-backend && python - <<'PY' ... from app.api.v1.endpoints.episodes import process_episode_generation_task ... PY` -> passed, printed `True`.

## Next Steps

- Continue committing the remaining logical change groups after this import blocker is resolved.

## Linked Commits

- Pending.
