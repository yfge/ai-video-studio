---
id: 2025-12-05T10-09-54Z-story-structure-crud
date: 2025-12-05T10:09:54Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, service, tests]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - ai-pic-backend/tests/test_story_structure_service.py
summary: "Add update/delete APIs for scenes/beats/shots and cover with service + endpoint tests"
---
## User Prompt
1. 拓展服务层：补充 scenes/beats/shots 的更新/删除接口，并暴露到 API。

## Goals
- Provide CRUD operations (update/delete) for scenes, scene beats, and shots; expose via API.
- Ensure tests cover aggregated creation and CRUD flows with the test DB setup.

## Changes
- Schemas: added `SceneUpdate`, `SceneBeatUpdate`, `ShotUpdate` for partial updates.
- Service: added update/delete helpers for scene/beat/shot; added create-with-children earlier; explicit child deletion on scene delete to avoid FK issues in SQLite.
- API: new endpoints for scene/beat/shot update and delete; added beat creation endpoint.
- Tests: added endpoint CRUD test `tests/test_story_structure_endpoints.py`, service aggregation test already present; test DB fixture now imports models before `create_all` to include story structure tables.

## Validation
- `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py tests/test_story_structure_service.py tests/test_user_management.py::TestUserRegistration -q`

## Next Steps
- Extend update/delete coverage to include ordering adjustments and validation (e.g., beat order reindexing), and wire auth/permissions if needed.

## Linked Commits
- (pending)
