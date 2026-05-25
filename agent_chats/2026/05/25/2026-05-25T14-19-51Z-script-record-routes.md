## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `scripts_legacy.py` by moving script list, record CRUD, and
  export endpoints into focused route modules.
- Preserve route order so static/generation paths still register before dynamic
  `/{script_id}` paths, and keep the no-trailing-slash bridge on the legacy
  router because FastAPI cannot include an empty subrouter path.

## Changes

- Added `app.api.v1.endpoints.scripts_lists` for script list and episode-list
  endpoints.
- Added `app.api.v1.endpoints.scripts_records` for script detail, update,
  soft-delete, and export endpoints.
- Added `app.api.v1.endpoints.scripts_route_utils` for shared soft-delete and
  script lookup helpers.
- Added `app.repositories.scripts_route_repository` so new route modules do not
  issue direct SQLAlchemy queries.
- Removed the moved route handlers from `scripts_legacy.py` and mounted the new
  routers after generation routes.
- Kept `get_scripts_no_slash` in `scripts_legacy.py` as a compatibility bridge
  to avoid FastAPI's empty-path include restriction.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_lists.py ai-pic-backend/app/api/v1/endpoints/scripts_records.py ai-pic-backend/app/api/v1/endpoints/scripts_route_utils.py ai-pic-backend/app/repositories/scripts_route_repository.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified catalog/generation
    paths stay before `/{script_id}`, with export and episode-list routes
    registered.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_soft_delete_api.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_lists.py ai-pic-backend/app/api/v1/endpoints/scripts_records.py ai-pic-backend/app/api/v1/endpoints/scripts_route_utils.py ai-pic-backend/app/repositories/scripts_route_repository.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-19-51Z-script-record-routes.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_lists.py ai-pic-backend/app/api/v1/endpoints/scripts_records.py ai-pic-backend/app/api/v1/endpoints/scripts_route_utils.py ai-pic-backend/app/repositories/scripts_route_repository.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-19-51Z-script-record-routes.md`
  - Passed.

## Next Steps

- Continue splitting `scripts_legacy.py`, with generation and regeneration task
  processing still the largest remaining block.

## Linked Commits

Pending
