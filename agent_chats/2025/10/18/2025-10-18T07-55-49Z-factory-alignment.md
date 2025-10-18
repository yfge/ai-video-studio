---
id: 2025-10-18T07-55-49Z-factory-alignment
date: 2025-10-18T07:55:49Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/tests/factories.py
summary: "Synced test factories with current SQLAlchemy models to avoid invalid fields"
---

## User Prompt
Install missing backend test deps (factory_boy, aiosqlite) and fix the app.main import so pytest passes; commit once tests are green.

## Goals
- Ensure episode/script/story character factories only populate columns that exist on the models.
- Prevent factory-based tests from raising `TypeError` during SQLAlchemy instantiation.

## Changes
- Replaced outdated episode payload keys with the current `plot_points`/`conflicts` schema.
- Updated script factory to emit `scenes`, `dialogues`, and `stage_directions` collections along with pagination metrics.
- Adjusted story character factory to align with `role_type`, `personality`, and `motivation` fields.

## Validation
- `pytest tests/test_models.py::TestEpisodeModel::test_create_episode -vv`

## Next Steps
- Run a broader pytest pass to catalogue remaining functional failures before deeper remediation.

## Linked Commits
- (pending)
