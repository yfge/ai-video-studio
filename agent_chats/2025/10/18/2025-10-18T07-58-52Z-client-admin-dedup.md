---
id: 2025-10-18T07-58-52Z-client-admin-dedup
date: 2025-10-18T07:58:52Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/tests/conftest.py
summary: "Prevent duplicated admin creation in pytest client fixture"
---

## User Prompt
Install missing backend test deps (factory_boy, aiosqlite) and fix the app.main import so pytest passes; commit once tests are green.

## Goals
- Avoid UNIQUE constraint violations on `users.username` introduced by repeated fixture setup.

## Changes
- Reused the existing `test_admin` account when constructing the test client, only inserting it once when absent.

## Validation
- `pytest tests/api/v1/test_diagnostic_endpoints.py::TestDiagnosticEndpoints::test_openai_test_endpoint_requires_auth -vv`

## Next Steps
- Differentiate authenticated vs unauthenticated client usage so auth-focused tests can assert 401 responses.

## Linked Commits
- (pending)
