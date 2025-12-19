---
id: 2025-12-19T03-25-00Z-refactor-story-structure-endpoint
date: 2025-12-19T03:25:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, api, refactor, phase3]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure/__init__.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/helpers.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/scenes.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/beats.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/shots.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environments.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_images.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/treatments.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/async_tasks.py
  - ai-pic-backend/app/services/task_worker.py
summary: "Refactored story_structure.py (1,318 lines) into modular package structure [Phase 3.3]"
---

## User Prompt

Continue with phase 3 endpoint refactoring (from context continuation).

## Goals

1. Split story_structure.py (1,318 lines) into smaller focused modules
2. Maintain all existing functionality for scenes, beats, shots, environments, and treatments
3. Update import references in task_worker.py
4. Verify production build passes

## Changes

### Created story_structure package structure:

1. **`helpers.py`** (~170 lines)
   - Shared utilities: `sanitize_environment_style`, `normalize_reference_images`, `infer_provider_from_model`, `strip_provider_prefix`, `compose_environment_prompt`, `download_and_attach`, `resolve_environment_url`

2. **`scenes.py`** (~110 lines)
   - Scene CRUD: `list_scenes_for_script`, `get_script_structure`, `create_scene_for_script`, `update_scene`, `delete_scene`, `seed_scenes_from_json`

3. **`beats.py`** (~80 lines)
   - Beat CRUD: `list_beats_for_scene`, `create_beat_for_scene`, `update_scene_beat`, `delete_scene_beat`

4. **`shots.py`** (~85 lines)
   - Shot CRUD: `list_shots_for_scene`, `create_shot_for_scene`, `update_shot`, `delete_shot`

5. **`environments.py`** (~100 lines)
   - Environment CRUD: `list_environments`, `get_environment`, `create_environment`, `update_environment`, `delete_environment`

6. **`environment_images.py`** (~145 lines)
   - Environment image CRUD: `list_environment_images`, `delete_environment_image`, `upload_environment_image`

7. **`environment_generation.py`** (~195 lines)
   - Text-to-image: `generate_environment_images`, `generate_environment_images_async`

8. **`environment_variants.py`** (~220 lines)
   - Image-to-image: `generate_environment_image_variants`, `generate_environment_image_variants_async`

9. **`async_tasks.py`** (~220 lines)
   - Background task processors: `process_environment_image_task`, `process_environment_image_variant_task`

10. **`treatments.py`** (~75 lines)
    - Story treatments: `list_treatments`, `create_treatment`, `list_step_outlines_for_treatment`, `create_step_outline_for_treatment`

11. **`__init__.py`** (~50 lines)
    - Router aggregation using direct route append pattern

### Updated imports:

1. **task_worker.py**: Changed imports from `_process_environment_image_task` to `process_environment_image_task` (removed underscore prefix)

### Deleted:
- `ai-pic-backend/app/api/v1/endpoints/story_structure.py` (original 1,318 line monolith)

## Validation

1. Ran pytest - passed (1 unrelated failure in diagnostic endpoints)
2. Ran production build `./docker/build_prod_images.sh` - PASSED

## Next Steps

1. Phase 3 endpoint refactoring complete for the primary targets
2. Consider additional refactoring for remaining large files in future phases

## Linked Commits

- TBD (commit will be created after this ledger entry)
