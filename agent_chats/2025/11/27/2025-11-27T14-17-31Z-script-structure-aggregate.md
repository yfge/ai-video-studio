---
id: 2025-11-27T14-17-31Z-script-structure-aggregate
date: 2025-11-27T14:17:31Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, service-layer]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - task.md
summary: "Added aggregated script structure endpoint returning scenes with beats and shots; aligned schemas and service grouping."
---

## User Prompt

- "continue"

## Goals

- Provide a nested read endpoint that returns scenes, beats, and shots for a script.
- Keep schemas and service code consistent with SQLite-friendly IDs and update the task board accordingly.

## Changes

- Added `/api/v1/story-structure/scripts/{script_id}/structure` with grouping/validation via new service helper and nested schemas.
- Grouped beats/shots by scene in service layer; schema now exposes `SceneWithChildren` and `ScriptStructureResponse`.
- Expanded endpoint tests to cover nested structure payload and refined task.md next step toward write flows.

## Validation

- `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py tests/scripts/test_prototype_story_structure_migration.py`

## Next Steps

- Implement aggregated write paths for scenes/beats/shots and tie into generation workflows.
- Re-run full pytest once upstream failing suites are addressed.

## Linked Commits

- (this commit)
