## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `scripts_legacy.py` with an atomic route-only split.
- Move script regeneration queue endpoints out of the legacy router while
  preserving route order and task-worker behavior.

## Changes

- Added `app.api.v1.endpoints.scripts_regeneration` for regeneration request
  schema, request payload construction, and task enqueue endpoints.
- Mounted the regeneration router from `scripts_legacy.py` after script record
  routes so existing dynamic record routes keep their behavior.
- Removed regeneration route handlers and task request-builder helpers from
  `scripts_legacy.py`.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_regeneration.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified generation routes stay
    before `/{script_id}`, regeneration routes are registered, and the no-slash
    bridge remains registered.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_story_structure_sync.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_regeneration.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-31-28Z-script-regeneration-routes.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_regeneration.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-31-28Z-script-regeneration-routes.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Continue splitting `scripts_legacy.py`; script generation and regeneration task
  processors remain the largest legacy block.

## Linked Commits

Pending
