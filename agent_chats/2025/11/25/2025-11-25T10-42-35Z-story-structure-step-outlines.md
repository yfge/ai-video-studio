---
id: 2025-11-25T10-42-35Z-story-structure-step-outlines
date: 2025-11-25T10:42:35Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, service-layer]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - task.md
summary: "Added step outline list/create endpoints with story/treatment validation and made story structure models SQLite-friendly for tests."
---
## User Prompt
- "check tasks and continue"

## Goals
- Expose step outline list/create APIs with story/treatment validation to progress the service-layer task.
- Ensure story structure models and schemas work under the SQLite test DB and reflect the next steps on the task board.

## Changes
- Added GET/POST step outline routes with treatment/story consistency checks and a service helper to fetch active treatments.
- Swapped story structure primary/foreign keys to SQLite-safe bigint variants and aligned response schemas to read `extra_metadata` instead of SQLAlchemy `metadata`.
- Expanded endpoint tests for step outline creation/validation and updated task.md with the next service-layer action.

## Validation
- `cd ai-pic-backend && pytest` (timed out around ~20% with pre-existing failures)
- `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py tests/scripts/test_prototype_story_structure_migration.py`

## Next Steps
- Add aggregated scenes/beats/shots read/write flows tied to treatments and clean up Pydantic config warnings.
- Re-run the full pytest suite once upstream failures are resolved or runtime budget allows.

## Linked Commits
- (this commit)
