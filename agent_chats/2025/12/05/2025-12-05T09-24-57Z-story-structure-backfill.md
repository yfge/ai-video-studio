---
id: 2025-12-05T09-24-57Z-story-structure-backfill
date: 2025-12-05T09:24:57Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/alembic/versions/c4a1cbf0d7c2_backfill_story_structure.py
  - ai-pic-backend/tests/test_user_management.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/unit/test_database.py
summary: "Backfill story structure via Alembic and stabilize user registration tests"
---

## User Prompt

完成迁移实现并补测试

## Goals

- Implement a data migration that normalizes existing script JSON into story structure tables.
- Add/repair tests around auth changes and test fixtures.

## Changes

- Added Alembic revision `c4a1cbf0d7c2_backfill_story_structure.py` to backfill `story_treatments/step_outlines/scenes/scene_beats/shots` using the prototype extractor; marks rows with `migration_revision` for downgrade cleanup.
- Test fixtures: added `db` alias, adjusted SQLite isolation level for tests, and set TestClient to use overridden DB.
- Auth tests: updated registration tests for first-user admin promotion, ensured table cleanup per test.

## Validation

- `cd ai-pic-backend && pytest tests/test_user_management.py::TestUserRegistration -q`

## Next Steps

- Run full `pytest` and `alembic upgrade c4a1cbf0d7c2` in a real DB to backfill data; downgrade will delete backfilled rows tagged with this revision.

## Linked Commits

- (pending)
