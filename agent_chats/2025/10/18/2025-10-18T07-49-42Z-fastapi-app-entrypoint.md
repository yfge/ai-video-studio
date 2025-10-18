---
id: 2025-10-18T07-49-42Z-fastapi-app-entrypoint
date: 2025-10-18T07:49:42Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/app/main.py
  - ai-pic-backend/main.py
  - ai-pic-backend/tests/conftest.py
summary: "Expose FastAPI app via package entrypoint and align test DB hooks for pytest"
---

## User Prompt
Install missing backend test deps (factory_boy, aiosqlite) and fix the app.main import so pytest passes; commit once tests are green.

## Goals
- Provide `app.main` module exporting the FastAPI app for test imports.
- Refactor root launcher to reuse the package-level app.
- Ensure pytest fixtures can import the shared DB override helpers without errors.

## Changes
- Added `ai-pic-backend/app/main.py` with application factory, shared logging, and router wiring.
- Simplified `ai-pic-backend/main.py` to import from `app.main` for CLI/uvicorn usage.
- Re-exported `get_test_db`/`override_get_db` via `tests/conftest.py`, sourcing from existing unit helpers.

## Validation
- `pytest` (ai-pic-backend) — suite still failing due to pre-existing fixture gaps (`driver`, `mock_ai_service`, etc.) and factory/model mismatches; first failure reported for missing e2e fixtures.

## Next Steps
- Stub or skip unavailable fixtures and align factories with current models so pytest can complete successfully.

## Linked Commits
- (pending)
