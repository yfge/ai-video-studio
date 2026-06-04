# Grid Storyboard Version Rebase

## User Prompt

Investigate and fix the failed `Timeline grid storyboard - 64` task. The visible
failure was `timeline version conflict` for a 9-panel grid storyboard generation
request.

## Goals

- Trace the failure to the real backend task path instead of guessing from the
  UI message.
- Keep the API-level expected-version conflict guard intact.
- Allow the async grid storyboard task to attach its support view when the
  Timeline version has advanced but the task's panel prompt snapshot still
  matches current Timeline clips.
- Reject stale tasks before provider image generation when the panel prompt
  snapshot no longer matches.

## Changes

- Added a row-locking repository read helper for applying Timeline updates from
  background tasks.
- Split grid storyboard sheet payload/rebase helpers into
  `app/services/storyboard/grid_storyboard_sheet_payload.py`.
- Updated `GridStoryboardSheetProcessor` to:
  - validate payload compatibility before provider generation,
  - preserve the payload's source Timeline version in support metadata,
  - reload and lock the current Timeline before writing the generated sheet,
  - rebase only when current panel prompt data still matches the task payload.
- Added processor regression tests for compatible rebase and stale-panel
  conflict behavior.
- Moved processor test fixtures into `tests/fixtures/grid_storyboard_processor.py`
  to keep files under repo size limits.

## Validation

1. Local checks:

- `docker logs --tail 80 ai-video-celery-worker | rg "timeline version conflict|grid_storyboard"` -> confirmed the failure was in `GridStoryboardSheetProcessor._process` at the async processor version check, not the submit API.
- MySQL inspection for task `6020` -> task payload had `timeline_id=64`, `expected_version=5`, `timeline_version=5`; Timeline `64` was already `version=7`, with revision `6` created at `2026-06-04 02:08:04`, before task failure at `2026-06-04 02:08:18`.
- `cd ai-pic-backend && pytest tests/test_timeline_storyboard_grid_processor.py -q` -> first new rebase test failed before implementation with `RuntimeError("timeline version conflict")`.
- `cd ai-pic-backend && pytest tests/test_timeline_storyboard_grid_api.py tests/test_timeline_storyboard_grid_processor.py -q` -> passed, `6 passed`.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/repositories/timeline_repository.py ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_processor.py ai-pic-backend/app/services/storyboard/grid_storyboard_sheet_payload.py ai-pic-backend/tests/test_timeline_storyboard_grid_processor.py ai-pic-backend/tests/fixtures/grid_storyboard_processor.py` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `docker restart ai-video-celery-worker` -> worker restarted and is `Up`.
- Dry-run compatibility check for failed task `6020` against current Timeline
  `64` -> `panel_snapshot_matches_current=False`; the old v5 task payload no
  longer matches current Timeline v8 and should not be replayed directly.

2. Browser or MCP validation:

- Not run. This change is backend task-processing behavior; the provider-backed
  browser path would create a real image generation task. The original failure
  was reproduced from Celery logs and task/Timeline DB state, and the regression
  was covered with processor/API tests.

3. Conflict signals and corrections:

- Initial assumption: the UI submission might have sent a stale expected version.
- Contradicting evidence: the task existed and failed inside Celery; DB payload
  showed it was queued from version `5`, while Timeline version advanced before
  processing.
- Correction: keep API conflict semantics, but rebase async support-view writes
  only when the task panel snapshot still matches current Timeline panel data.
- Additional validation note: `cd ai-pic-backend && python run_tests.py quick`
  failed during dependency setup before tests because the current Python 3.13
  environment cannot resolve `pydantic==2.5.0` with
  `langchain-core==0.2.43` requiring `pydantic>=2.7.4`. A follow-up
  `python run_tests.py quick --no-setup` was started but blocked in Selenium
  manager during broad non-slow tests and was terminated; this is outside the
  targeted backend task path.

## Next Steps

- Rerun the grid storyboard generation from the UI after backend worker reload so
  the task uses the updated processor code and current Timeline version.
- If full quick validation is required later, fix or isolate the Python 3.13
  dependency-resolution issue in the repo test runner first.

## Linked Commits

- Pending.
