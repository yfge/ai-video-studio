---
id: 2026-06-03T08-37-09Z-celery-grid-storyboard-import-cycle
date: "2026-06-03T08:37:09Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, celery, storyboard]
related_paths:
  - ai-pic-backend/app/services/timeline_clip_asset_lineage.py
  - ai-pic-backend/tests/unit/services/test_celery_task_imports.py
summary: "Break Celery grid storyboard import cycle"
---

## User Prompt

User reported a Celery beat startup traceback ending in an import cycle:
`task_worker_grid_storyboard -> grid_storyboard_sheet_processor -> timeline_clip_asset_lineage -> app.services.render -> timeline_render_output -> timeline_clip_asset_lineage`.

## Goals

- Reproduce the Celery startup import failure locally.
- Remove the import cycle without widening the grid-storyboard task surface.
- Add a regression test for the Celery import path.
- Run focused backend validation and repo checks.

## Changes

- Changed `app.services.timeline_clip_asset_lineage` to import `TimelineClipVideo` only under `TYPE_CHECKING`; the module already uses postponed annotations, so this removes a runtime dependency on the eager `app.services.render` package initializer.
- Added `tests/unit/services/test_celery_task_imports.py` to import `app.core.celery_app` in a clean Python subprocess and assert the grid-storyboard task is registered.

## Validation

1. Local checks:

- `cd ai-pic-backend && python - <<'PY' ... import app.services.timeline_clip_asset_lineage ... PY` -> reproduced the reported `ImportError: cannot import name 'TimelineClipAssetLineageService' from partially initialized module`.
- `cd ai-pic-backend && pytest tests/unit/services/test_celery_task_imports.py -q` before the fix -> failed with the same Celery startup import cycle.
- `cd ai-pic-backend && pytest tests/unit/services/test_celery_task_imports.py -q` after the fix -> passed, `1 passed`.
- `cd ai-pic-backend && python - <<'PY' ... from app.core.celery_app import celery_app ... PY` -> passed, printed `grid_task_registered True`.
- `cd ai-pic-backend && pytest tests/unit/services/test_celery_task_imports.py tests/test_timeline_storyboard_grid_processor.py -q` -> passed, `2 passed`.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/timeline_clip_asset_lineage.py ai-pic-backend/tests/unit/services/test_celery_task_imports.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/timeline_clip_asset_lineage.py ai-pic-backend/tests/unit/services/test_celery_task_imports.py agent_chats/2026/06/03/2026-06-03T08-37-09Z-celery-grid-storyboard-import-cycle.md` -> passed.

2. Browser or MCP validation:

- Not run; this was a backend Celery import/startup fix with no frontend path.

3. Conflict signals and corrections:

- Initial assumption: an in-process pytest import test would reproduce the startup failure.
- Contradicting evidence: the first pytest test passed because pytest module ordering masked the cycle.
- Reproduction and fix: changed the regression test to use a clean Python subprocess, which reproduced the container startup traceback before the code fix.
- Final verified state: clean subprocess import of `app.core.celery_app` succeeds and the grid-storyboard task is registered.

Additional validation note:

- `cd ai-pic-backend && python run_tests.py quick` was started but produced no output for several minutes in this local environment; the hung `python run_tests.py quick` process was terminated and no orphaned pytest/run_tests process remained.

## Next Steps

- Restart the affected Celery beat/worker containers so they load the updated import graph.
- Re-run the full backend quick gate in a non-hanging environment if this branch is being prepared for commit/PR.

## Linked Commits

- Not committed.
