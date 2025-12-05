---
id: 2025-12-05T09-39-15Z-story-structure-service
date: 2025-12-05T09:39:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, service, tests]
related_paths:
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/tests/test_story_structure_service.py
summary: "Add aggregated scene creation and tests for story structure services"
---
## User Prompt
服务层改造：更新生成/查询 Service 与 Repository，提供分层读取与写入接口

## Goals
- Provide a service helper to create scenes with beats/shots in one call and ensure aggregated retrieval works.
- Add tests to cover the aggregated flow.

## Changes
- `create_scene_with_children` in `story_structure_service` now creates a scene plus beats and shots (maps shots to beats by order when IDs are absent) in a single transaction.
- Added `tests/test_story_structure_service.py` to validate the aggregated create + `get_script_structure` path.

## Validation
- `cd ai-pic-backend && pytest tests/test_story_structure_service.py -q` (pass).

## Next Steps
- Expand service methods to cover updates/deletes and integrate with API endpoints as needed.

## Linked Commits
- (pending)
