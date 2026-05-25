## User Prompt

commit 然后继续，直到所有完成

## Goals

- Move script regeneration worker processing out of `scripts_legacy.py`.
- Keep new service files below repository size limits and keep DB lookup behind
  repositories.

## Changes

- Added `app.services.script.regeneration_task_processor` for the Celery
  regeneration processor.
- Added `app.services.script.regeneration_generation` and
  `regeneration_task_helpers` to keep generation, persistence, task status, and
  scene-budget helper logic split below service limits.
- Added `ScriptsRouteRepository.get_regeneration_script` for the regeneration
  worker lookup.
- Updated `app.services.task_worker.script_regenerate_task` to dispatch directly
  to the service processor.
- Kept `_process_script_regeneration_task` compatibility via a legacy-module
  alias, while `task_worker` no longer imports the legacy router package.
- Updated the mock AI fixture to patch the new regeneration generation service.
- Removed the old regeneration processor from `scripts_legacy.py`.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py ai-pic-backend/app/services/task_worker.py ai-pic-backend/app/services/script/regeneration_generation.py ai-pic-backend/app/services/script/regeneration_task_processor.py ai-pic-backend/app/services/script/regeneration_task_helpers.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: verified `_process_script_regeneration_task` compatibility export
    points to `process_script_regeneration_task`.
- `cd ai-pic-backend && pytest tests/scripts/test_script_story_structure_sync.py tests/test_api.py::TestScriptAPI -q`
  - Passed: 5 tests.
- `cd ai-pic-backend && pytest tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old -q`
  - Passed: 1 test.
- `cd ai-pic-backend && pytest tests/scripts/test_script_story_structure_sync.py tests/scripts/test_script_regeneration_soft_delete.py tests/test_api.py::TestScriptAPI -q`
  - Passed: 6 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/services/task_worker.py ai-pic-backend/app/services/script/regeneration_generation.py ai-pic-backend/app/services/script/regeneration_task_processor.py ai-pic-backend/app/services/script/regeneration_task_helpers.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T15-10-36Z-script-regeneration-processor.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/services/task_worker.py ai-pic-backend/app/services/script/regeneration_generation.py ai-pic-backend/app/services/script/regeneration_task_processor.py ai-pic-backend/app/services/script/regeneration_task_helpers.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T15-10-36Z-script-regeneration-processor.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Move the async script generation worker processor out of `scripts_legacy.py`;
  it is the last large legacy block.

## Linked Commits

Pending
