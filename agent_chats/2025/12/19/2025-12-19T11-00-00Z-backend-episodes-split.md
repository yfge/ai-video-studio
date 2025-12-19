---
id: 2025-12-19T11-00-00Z-backend-episodes-split
date: 2025-12-19T11:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, python, phase3]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/crud.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/generation.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/regenerate.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/helpers.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/api/test_episode_outline_persistence.py
  - ai-pic-backend/tests/unit/test_episode_scene_fallback.py
summary: "Split episodes.py (1,605 lines) into modular structure [phase3.1]"
---

## User Prompt

Continue executing refactoring plan Phase 3.1 - Split Backend Episode Endpoints.

## Goals

1. Split monolithic episodes.py (1,605 lines) into focused modules
2. Organize endpoints by concern: CRUD, generation, regeneration, async tasks
3. Extract helper functions to shared helpers.py
4. Maintain backward compatibility with existing imports
5. Update test files to use new module structure

## Changes

### New Module Structure (6 files created)

```
episodes/
├── __init__.py         (~60 lines) - Router aggregation and exports
├── crud.py             (~280 lines) - CRUD endpoints
├── generation.py       (~300 lines) - AI episode generation
├── regenerate.py       (~160 lines) - Episode regeneration
├── async_tasks.py      (~450 lines) - Background task processing
└── helpers.py          (~360 lines) - Shared utilities
```

### Module Details

1. **helpers.py** (~360 lines)
   - `not_deleted` - Soft delete query filter
   - `get_episode_by_identifier` - Get episode by ID or business_id
   - `get_story_by_identifier` - Get story by ID or business_id
   - `is_episode_payload_valid` - Validate episode data
   - `parse_step_outlines` - Parse AI-generated outlines
   - `persist_story_outlines` - Save outlines to story metadata
   - `build_outline_rows` - Build StoryStepOutlineCreate rows
   - `build_stub_episodes_from_outlines` - Fallback episode creation
   - `update_task_progress` - Update task description
   - `ensure_scenes` - Ensure episode has valid scenes

2. **crud.py** (~280 lines)
   - POST `/` - Create episode
   - GET `/`, GET `` - List episodes
   - GET `/{episode_id}` - Get by ID
   - GET `/business/{business_id}` - Get by business ID
   - PUT `/{episode_id}`, PUT `/business/{business_id}` - Update
   - DELETE `/{episode_id}`, DELETE `/business/{business_id}` - Delete
   - GET `/story/{story_id}`, GET `/story/business/{business_id}` - Get by story

3. **generation.py** (~300 lines)
   - POST `/generate` - AI episode generation (sync)
   - POST `/prompt/preview` - Preview generation prompt
   - Helper: `_build_story_data`, `_get_focus_characters`, `_build_agent_run_info`

4. **regenerate.py** (~160 lines)
   - POST `/{episode_id}/regenerate` - Regenerate episode by ID
   - POST `/business/{business_id}/regenerate` - Regenerate by business ID
   - Helper: `_regenerate_episode_instance`

5. **async_tasks.py** (~450 lines)
   - POST `/generate-async` - Async episode generation
   - `process_episode_generation_task` - Celery task processor
   - `_process_fallback_result` - Handle non-callback results
   - `_coerce_episode_payload` - Normalize episode data

6. **__init__.py** (~60 lines)
   - Aggregates all sub-routers into single `router`
   - Re-exports helpers and `process_episode_generation_task`

### Updated Files

- **task_worker.py**: Updated import from `_process_episode_generation_task` to `process_episode_generation_task`
- **tests/conftest.py**: Updated to patch ai_service in all episode submodules
- **tests/api/test_episode_outline_persistence.py**: Updated import to use `generation` submodule
- **tests/unit/test_episode_scene_fallback.py**: Updated import to use `ensure_scenes` (no underscore)

### Deleted Files

- **episodes.py**: Removed after successful migration (1,605 lines → 6 modular files)

## Validation

1. **Module Import**: `from app.api.v1.endpoints.episodes import router` - 16 routes loaded
2. **Unit Tests**: `test_episode_scene_fallback.py` - PASSED
3. **API Tests**: `test_episode_outline_persistence.py` - 2 tests PASSED
4. **Production Build**: `./docker/build_prod_images.sh` - SUCCESS

## Next Steps

1. Phase 3.2: Refactor virtual_ip_images.py (1,364 lines)
2. Phase 3.3: Refactor story_structure.py (1,318 lines)

## Linked Commits

- To be linked after commit
