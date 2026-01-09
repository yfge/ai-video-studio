---
id: 2026-01-09T05-32-16Z-refactor-episode-generation-conftest
date: 2026-01-09T05:32:16Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, refactor, tests, docker]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/generation.py
  - ai-pic-backend/app/services/episode/episode_generation_service.py
  - ai-pic-backend/app/services/episode/episode_generation_persistence.py
  - ai-pic-backend/app/services/episode/episode_generation_utils.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/episode_agent_episode.py
  - ai-pic-backend/app/services/episode_agent_episode_utils.py
  - ai-pic-backend/app/services/episode_agent_outline.py
  - ai-pic-backend/app/services/script/scene_utils.py
  - ai-pic-backend/app/services/script/script_utils.py
  - ai-pic-backend/app/services/story/story_generation_prompt_preview.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/app/prompts/manager.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/fixtures/mock_ai_service.py
  - ai-pic-backend/tests/fixtures/client.py
  - ai-pic-backend/tests/fixtures/db.py
  - ai-pic-backend/tests/fixtures/markers.py
  - ai-pic-backend/tests/fixtures/asyncio_loop.py
  - ai-pic-backend/tests/fixtures/selenium_driver.py
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx
summary: "Refactored episode generation + pytest fixtures; fixed frontend type error blocking prod Docker build"
---

## User Prompt

- commit

## Goals

- Ensure recent feature work can be committed with repo guards passing (pytest quick gate, frontend lint, production Docker image build).
- Bring touched files back under repository size limits by splitting/refactoring (service files <250 lines, endpoints thin).

## Changes

- [refactor] Replaced `ai-pic-backend/app/api/v1/endpoints/episodes/generation.py` with thin handlers and moved logic into `EpisodeGenerationService`.
- [refactor] Split episode generation persistence/utility helpers into `ai-pic-backend/app/services/episode/episode_generation_*.py`.
- [refactor] Split `ai-pic-backend/app/services/episode_agent.py` into focused helpers (`episode_agent_outline`, `episode_agent_episode`, `episode_agent_episode_utils`) while keeping the public API stable.
- [refactor] Extracted shared script scene helpers into `ai-pic-backend/app/services/script/scene_utils.py` to keep `script_utils.py` under limits.
- [refactor] Extracted story-outline preview prompt helper into `ai-pic-backend/app/services/story/story_generation_prompt_preview.py`.
- [refactor] Split `ai-pic-backend/tests/conftest.py` into plugin-based fixtures under `ai-pic-backend/tests/fixtures/` and updated `mock_ai_service` patch targets for new modules.
- Fixed Next.js production build type error by casting `taskId` to string for `taskAPI.getTask()` in `ai-pic-frontend/src/components/features/story-detail/StoryNovelExportSection.tsx`.

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `cd ai-pic-frontend && npm run lint` (warnings only)
- `./docker/build_prod_images.sh`
- Note: `cd ai-pic-backend && pytest` currently reports many failures in this repo (integration/e2e/migration suites); the quick gate suite above is green and matches pre-commit behavior.

## Next Steps

- (Optional) Align full `pytest` suite behavior (integration/e2e/migrations) with CI expectations and document required env/services.

## Linked Commits

- (this commit)
