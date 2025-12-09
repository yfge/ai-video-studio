---
id: 2025-12-09T03-15-10Z-scene-propagation
date: 2025-12-09T03:15:10Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, frontend, scenes]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/prompts/templates/script_generation.txt
  - ai-pic-backend/tests/scripts/test_script_story_structure_sync.py
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Propagate episode scene metadata into script generation/prompting and surface scene previews in story list; keep normalized scenes in sync."
---

## User Prompt

完成场景集成在故事，剧本，分镜中的工作

## Goals

- Ensure episode-level scenes flow into script generation and normalization so storyboard can use them immediately.
- Include episode scenes in script prompts and default fallback when providers omit scenes.
- Surface episode scene previews/counts in story list UI.
- Keep regression coverage for scene sync across async/sync generation.

## Changes

- Backend: added `_extract_episode_scenes` and feed episode scenes/scene_count into `_build_episode_data`; `_normalize_script_content` now accepts `default_scenes` fallback and enriches metadata. Script generation/regeneration/async paths now use episode scenes as defaults. Script prompt template includes pre-set episode scenes.
- Tests: expanded `test_script_story_structure_sync` to cover episode.extra_metadata scenes fallback, ensured script.scenes populated and normalized scenes/shots count stable after regenerate.
- Frontend: episode/story API types include `extra_metadata`; story list shows scene count derived from metadata and previews first scenes.

## Validation

- `cd ai-pic-backend && pytest tests/scripts/test_script_story_structure_sync.py`
- `cd ai-pic-frontend && npm run lint`
- Chrome self-test (MCP/DevTools): login `geyunfei`/`Gyf@845261` → open `http://localhost:8089/episodes/8` → verified scene_count=6 with structured scene cards rendered from episode metadata after recent changes.

## Next Steps

- Propagate normalized scene IDs/environment bindings into storyboard generation payloads and meta scopes.
- Add snapshot tests for script prompt rendering with episode scenes included.

## Linked Commits

- (pending)
