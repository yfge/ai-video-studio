---
id: 2025-10-18T07-54-40Z-pytest-fixture-stabilization
date: 2025-10-18T07:54:40Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/tests/conftest.py
summary: "Added pytest fixtures and dependency overrides to unblock backend suite collection"
---

## User Prompt
Install missing backend test deps (factory_boy, aiosqlite) and fix the app.main import so pytest passes; commit once tests are green.

## Goals
- Provide missing pytest fixtures (`driver`, `mock_ai_service`, `test_db_session`) expected by the suite.
- Ensure FastAPI dependency overrides yield an approved admin user for auth-guarded endpoints.
- Guarantee fixture behavior is skip-friendly when optional tooling is absent.

## Changes
- Added mock AI service returning deterministic payloads and temporary assets.
- Introduced Selenium driver fixture with automatic skip fallback.
- Wired shared DB session for `test_db_session` fixture and overrode auth dependencies in the client fixture for smoother API tests.

## Validation
- `pytest tests/test_models_simple.py::test_create_story -vv`

## Next Steps
- Update factory definitions to match current SQLAlchemy models and eliminate invalid keyword errors.

## Linked Commits
- (pending)
