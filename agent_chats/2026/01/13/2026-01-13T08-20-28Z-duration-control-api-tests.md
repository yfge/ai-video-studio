---
id: 2026-01-13T08-20-28Z-duration-control-api-tests
date: 2026-01-13T08:20:28Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, tests, duration-orchestrator]
related_paths:
  - ai-pic-backend/tests/integration/test_duration_control_api.py
  - tasks.md
summary: "Added duration control API integration tests and marked Phase 6.5 complete"
---

## User Prompt
6.5

## Goals
- Add API integration tests for duration control tasks.
- Mark Phase 6.5 as completed in the task board.

## Changes
- Added integration tests covering duration-controlled dialogue audio tasks and timeline pipeline tasks.
- Verified async endpoint stores `use_duration_control` in task parameters.
- Updated Phase 6.5 in `tasks.md` to completed.

## Validation
- `cd ai-pic-backend && pytest` (fails: 92 failed, 7 errors; existing suite failures).
- `cd ai-pic-backend && pytest tests/integration/test_duration_control_api.py -vv`.
- `./docker/build_prod_images.sh`.
- Chrome E2E: not run (tests-only change).

## Next Steps
- Resolve existing pytest failures blocking full suite.
- Run Chrome E2E flows when functional changes land.

## Linked Commits
- test(backend): add duration control api integration tests
