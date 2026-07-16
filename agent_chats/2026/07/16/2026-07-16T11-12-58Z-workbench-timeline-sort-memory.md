---
id: 2026-07-16T11-12-58Z-workbench-timeline-sort-memory
date: "2026-07-16T11:12:58Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - workbench
  - backend
  - timeline
  - mysql
  - browser-validation
related_paths:
  - ai-pic-backend/app/repositories/timeline_repository.py
  - ai-pic-backend/tests/unit/repositories/test_timeline_repository.py
  - artifacts/runs/workbench-sort-memory-fix-20260716T1113Z/
summary: Keep large Timeline JSON specs out of the latest-version sort so the operator workbench loads under the live MySQL sort-buffer limit.
---

## User Prompt

工作台现在出错

## Goals

- Reproduce the current operator-workbench failure from the running application.
- Identify the backend root cause rather than treating the browser CORS message as
  the primary failure.
- Fix the shared latest-Timeline lookup without changing MySQL configuration or
  adding an emergency schema migration.
- Validate the live API and visible workbench while preserving unrelated Canvas
  worktree changes.

## Changes

- Changed `TimelineRepository.get_latest_for_episode_script` to sort and select
  only `Timeline.id`, then load the complete Timeline by primary key.
- Added a repository regression test that captures SQL and asserts the ordered
  projection excludes the large `timelines.spec` JSON column.
- Kept the fix in the shared repository method so workbench, Canvas, storyboard,
  import, and render callers use the same safe lookup.

## Validation

1. Reproduction and root cause:

- Authenticated Playwright reproduction opened `http://localhost:8090/` and showed
  `Failed to fetch`.
- Browser Console reported CORS because the direct backend response lacked CORS
  headers after an unhandled failure; direct authenticated
  `GET /api/v1/workbench/summary` returned HTTP 500.
- Running `WorkbenchService.summary_for_user(1)` inside `ai-video-backend` produced
  MySQL error `1038: Out of sort memory` from
  `get_latest_for_episode_script`.
- The failing Timeline row had a `491336`-byte JSON `spec`; MySQL
  `sort_buffer_size` was `262144`, and `EXPLAIN` showed `Using filesort`.

2. Automated backend:

- `cd ai-pic-backend && pytest tests/unit/repositories/test_timeline_repository.py tests/integration/test_workbench_summary_api.py -v`
  -> `5 passed`.
- `cd ai-pic-backend && python run_tests.py quick`
  -> did not reach tests because the Python 3.13 dependency setup could not resolve
  repository pins: `pydantic==2.5.0` conflicts with
  `langchain-core==0.2.43` requiring `pydantic>=2.7.4`.
- `ruff check app/repositories/timeline_repository.py tests/unit/repositories/test_timeline_repository.py`
  -> passed.
- `git diff --check` for the two backend paths -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- Changed-file repository contract check -> passed.
- Scoped pre-commit backend gate -> `2218 passed, 59 skipped`.
- The scoped pre-commit command returned nonzero after the passing checks because
  ledger enforcement detected the unrelated existing Canvas ledger and another
  concurrent Canvas pre-commit modified the worktree while the backend hook ran.
  No unrelated changes were reverted or staged.

3. Live API and browser:

- The running backend hot-reloaded the repository change.
- Authenticated live `GET http://127.0.0.1:8000/api/v1/workbench/summary`
  changed from HTTP 500 to HTTP 200 and returned 8 recent episodes plus 8 task
  queue entries.
- Preferred Chrome DevTools connection at `127.0.0.1:9222` timed out, so the
  repository harness recorded a Playwright fallback as `degraded`, not Chrome
  verification.
- Evidence run:
  `artifacts/runs/workbench-sort-memory-fix-20260716T1113Z/`.
- Playwright loaded the full workbench with the production-state cards, recent
  episodes, and task queue visible. Console had no errors or warnings.
- The final two `/api/v1/workbench/summary` responses were HTTP 200. Earlier
  `ERR_ABORTED` entries were requests cancelled during login navigation.

## Next Steps

- Repair the local Chrome DevTools endpoint if non-degraded Chrome evidence is
  required.
- Fix or isolate the backend quick-gate dependency resolver for Python 3.13.
- Add a composite Timeline lookup index only if query-volume measurements justify
  a migration; the current primary-key projection removes the immediate failure.

## Linked Commits

- Included in this commit.
