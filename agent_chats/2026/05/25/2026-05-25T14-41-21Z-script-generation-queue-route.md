## User Prompt

commit 然后继续，直到所有完成

## Goals

- Move the operator-facing `/scripts/generate-async` queue endpoint out of
  `scripts_legacy.py`.
- Preserve production-mode defaults and Celery task dispatch behavior.

## Changes

- Added `app.api.v1.endpoints.scripts_generation_queue` for async script
  generation task creation and request parameter normalization.
- Mounted the generation queue router before dynamic script record routes.
- Removed `/generate-async` from `scripts_legacy.py` and dropped its now-unused
  task worker import.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_queue.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified `/generate-async` and
    `/generate` register before `/{script_id}`.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run tests/test_api.py::TestScriptAPI -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_queue.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-41-21Z-script-generation-queue-route.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_queue.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-41-21Z-script-generation-queue-route.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Continue splitting `scripts_legacy.py`; synchronous generation and worker task
  processors remain the largest legacy block.

## Linked Commits

Pending
