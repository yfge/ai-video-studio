## User Prompt

PLEASE IMPLEMENT THIS PLAN: Fix Timeline Pipeline Silent Clip Failure. Scope is only the `timeline_pipeline` failure for task `6006` / `script 128`; do not touch separate `episode 153` script-generation failures or unrelated dirty work.

## Goals

- Allow Timeline shot-plan generation to accept silent `pause` / placeholder video clips with empty `plot` and `dialogue_source`.
- Keep source-backed non-pause clips protected from empty story/dialogue shot-plan data.
- Persist useful timeline pipeline task errors when the failing exception is an `HTTPException`.
- Preserve unrelated dirty work in the repository.

## Changes

- Relaxed `TimelineShot.plot` and `TimelineShot.dialogue_source` model-level requirements, then added Timeline-context validation so source-backed clips still require non-empty plot/dialogue fields.
- Treated action clips without a speaker as non-dialogue source material, so they still require `plot` but may keep `dialogue_source=""`.
- Clarified the shot-plan prompt so silent pause/placeholder clips must not invent dialogue and may keep empty text fields when the source clip has no text.
- Added pipeline error formatting that prefers `HTTPException.detail`, JSON-serializes structured details, and falls back to the exception class name when no message exists.
- Converted Pydantic validation errors in shot-plan service responses to JSON-safe API details and increased the generation token budget based on video clip count.
- Fixed repeat-overwrite audio timeline reads/writes by ignoring soft-deleted scene beats in repository reads and pruning stale soft-deleted duplicates before inserting replacement beats.
- Added focused tests for silent pause clips, action clips without dialogue, source-backed invalid clips, repeat-overwrite soft-delete handling, and persisted pipeline `HTTPException.detail`.

## Validation

- `cd ai-pic-backend && pytest tests/unit/repositories/test_audio_timeline_repository.py tests/test_timeline_shot_plan_api.py tests/test_timeline_shot_plan_silent_clips.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py -q` passed in the current workspace: 12 passed.
- `python scripts/check_repo_docs.py` passed: `[check_repo_docs] ok`.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed: `[check_repo_contracts] ok (diff)`.
- `cd ai-pic-backend && python run_tests.py quick` previously hit the known local Python 3.13 dependency resolver conflict (`pydantic==2.5.0` vs `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on Python 3.12.4+); the final repeat attempt emitted no output for more than 3 minutes before being terminated, so it did not enter the test phase.
- Chrome DevTools transport was unavailable locally, so browser runtime checks used Playwright with system Chrome as fallback. Browser-triggered Celery attempts exposed repeat-overwrite soft-delete issues and local worker/provider instability before the direct backend fallback.
- Direct backend fallback with the pipeline's default `TimelineShotPlanRequest` succeeded on `timeline_id=64`: version `8`, 17 video clips, 2 pause clips, 17 `timeline_shot_plan` entries, and both pause clips retained `dialogue_source=""`. Evidence: `artifacts/runs/20260604T020337Z-timeline-pipeline-sync-handler-reuse-audio/direct-shot-plan-default-success.json`.
- Restarted local services with `docker compose -f docker-compose.dev.yml restart ai-video-backend ai-video-celery-worker`; `docker compose ... ps` showed both `ai-video-backend` and `ai-video-celery-worker` as `Up`.

## Next Steps

- Full one-click Celery completion remains sensitive to the local long-running worker lifecycle and provider response stability; restart backend/Celery before another UI run if the worker has been running through code changes.
- `episode 153` script-generation failures remain intentionally out of scope.

## Linked Commits

- Pending commit.
