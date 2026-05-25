## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue the main-chain cleanup plan with an atomic commit.
- Move async script generation worker processing out of `scripts_legacy.py`.
- Keep the legacy router as a thin compatibility/mounting surface only.
- Preserve existing async generation behavior and targeted regression coverage.

## Changes

- Moved async script generation Celery processing into
  `app.services.script.generation_task_processor`.
- Split async generation helpers into focused modules:
  - `generation_task_context.py`
  - `generation_task_attempts.py`
  - `generation_task_persistence.py`
- Updated `task_worker.script_generate_task` to dispatch directly to the service
  instead of importing the legacy router package.
- Added a repository lookup for async task episode ownership checks.
- Updated script tests and mock AI fixture to patch the current service modules
  instead of stale `scripts_legacy.py` bindings.
- Updated `tasks.md` and the main-chain readiness plan to record the split.

## Validation

1. Local checks:

- `cd ai-pic-backend && python -m py_compile app/api/v1/endpoints/scripts_legacy.py app/services/task_worker.py app/services/script/generation_task_processor.py app/services/script/generation_task_attempts.py app/services/script/generation_task_persistence.py app/services/script/generation_task_context.py app/repositories/scripts_route_repository.py tests/fixtures/mock_ai_service.py` -> passed.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run tests/scripts/test_script_story_structure_sync.py tests/scripts/test_script_regeneration_soft_delete.py tests/test_api.py::TestScriptAPI -q` -> first run failed because tests still monkeypatched stale legacy-router quality-gate bindings; tests were updated to patch the current service modules.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run tests/scripts/test_script_story_structure_sync.py tests/scripts/test_script_regeneration_soft_delete.py tests/test_api.py::TestScriptAPI -q` -> passed, 7 tests, warnings only.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files <changed files>` -> passed, including backend quick gate; frontend lint skipped because no frontend files were changed.

2. Browser or MCP validation:

- Not run. This slice changes backend worker/service factoring and tests only; it does not change frontend routes, login, browser-visible controls, or provider media generation behavior.

3. Conflict signals and corrections:

- Initial split removed the old `scripts_legacy.py` `ai_service` and quality-gate bindings.
- Existing tests contradicted that by patching the stale legacy module.
- Tests were corrected to patch `app.services.script.sync_generation` and
  `app.services.script.regeneration_generation`, matching the current execution path.
- A behavior drift was caught during review: standard non-production generation was
  briefly changed to always run scoring. The guard was restored so scoring runs
  only when marketing metadata exists, matching the previous behavior.

## Next Steps

- Finish submit gates and commit this script generation processor split.
- Continue legacy main-chain cleanup until no major user path depends on
  `scripts_legacy.py`.

## Linked Commits

Pending
