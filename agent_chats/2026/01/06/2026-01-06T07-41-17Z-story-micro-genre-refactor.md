---
id: 2026-01-06T07-41-17Z-story-micro-genre-refactor
date: 2026-01-06T07:41:17Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, api, refactor, story, micro-genre]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/stories/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/stories/helpers.py
  - ai-pic-backend/app/api/v1/endpoints/stories/crud.py
  - ai-pic-backend/app/api/v1/endpoints/stories/characters.py
  - ai-pic-backend/app/api/v1/endpoints/stories/generation.py
  - ai-pic-backend/app/api/v1/endpoints/stories/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/stories/meta.py
  - ai-pic-backend/app/prompts/templates/story_outline.txt
  - ai-pic-backend/app/prompts/templates/story_outline.yaml
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/ai/__init__.py
  - ai-pic-backend/app/services/ai/base.py
  - ai-pic-backend/app/services/ai/episodes.py
  - ai-pic-backend/app/services/ai/episodes_mock.py
  - ai-pic-backend/app/services/ai/episodes_mock_script.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/ai/images_ops.py
  - ai-pic-backend/app/services/ai/images_providers.py
  - ai-pic-backend/app/services/ai/images_storage.py
  - ai-pic-backend/app/services/ai/manager.py
  - ai-pic-backend/app/services/ai/model_ui.py
  - ai-pic-backend/app/services/ai/models.py
  - ai-pic-backend/app/services/ai/scripts.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/services/ai/service.py
  - ai-pic-backend/app/services/ai/speech.py
  - ai-pic-backend/app/services/ai/story_outline.py
  - ai-pic-backend/app/services/ai/storyboard_generation.py
  - ai-pic-backend/app/services/ai/storyboard_plan.py
  - ai-pic-backend/app/services/ai/storyboard_utils.py
  - ai-pic-backend/app/services/ai/text_generation.py
  - ai-pic-backend/app/services/ai/video.py
  - ai-pic-backend/app/services/story/__init__.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/services/story_agent.py
summary: "Refactored AI service modules and extended story generation metadata for micro-genre hook/ad outputs."
---

## User Prompt

- Start the micro-genre and ad-driven creation loop feature, refactor oversized files first, ensure full E2E validation, and keep atomic commits with a clean workspace.

## Goals

- Split oversized AI service and story endpoints into compliant modules.
- Add micro-genre, hook plan, cliffhanger, and ad snippet outputs to story generation.
- Validate via UI flow and API payload inspection.

## Changes

- Replaced monolithic AI service with a modular package and a thin compatibility wrapper.
- Split story endpoints into focused modules with shared helper logic.
- Added story generation service and expanded schema/prompt templates to capture hook plans and ad snippets.

## Validation

- Chrome MCP: logged into `http://localhost:8089`, generated story "微类型钩子验证", opened story detail page, and confirmed creation succeeded.
- API check: `GET /api/v1/stories/business/90d90dea749448ffa40bcfdce8bc9711` showed `extra_metadata.hook_plan`, `twist_density`, `cliffhanger_plan`, `ad_snippets`, and `generation_params` containing `micro_genre`/`market_region` fields.
- `pytest` (ai-pic-backend) failed (89 failed, 13 errors) with missing fixtures and multiple API/model failures.
- `./docker/build_prod_images.sh` succeeded for backend/frontend images.

## Next Steps

- Investigate and resolve failing pytest suite (missing fixtures and API expectations).
- Consider exposing micro-genre and hook/ad metadata in UI if needed.

## Linked Commits

- TBD
