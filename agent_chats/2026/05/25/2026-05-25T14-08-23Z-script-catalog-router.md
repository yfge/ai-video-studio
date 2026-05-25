## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `scripts_legacy.py` without changing route behavior.
- Move stateless script catalog endpoints out of the legacy router while
  preserving route order ahead of dynamic `/{script_id}` paths.

## Changes

- Added `app.api.v1.endpoints.scripts_catalog`.
- Moved `/scripts/formats` and `/scripts/languages` route handlers out of
  `scripts_legacy.py`.
- Mounted the catalog router inside `scripts_legacy.py` immediately after router
  creation so static catalog paths remain before dynamic script-id routes.
- Updated `tasks.md` and the active commercial readiness plan with the split.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_catalog.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified `/formats` and
    `/languages` are registered before `/{script_id}`.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_soft_delete_api.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_catalog.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-08-23Z-script-catalog-router.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_catalog.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-08-23Z-script-catalog-router.md`
  - Passed.

## Next Steps

- Continue splitting `scripts_legacy.py`, prioritizing CRUD/export and generation
  task helpers behind stable subrouters/services.

## Linked Commits

Pending
