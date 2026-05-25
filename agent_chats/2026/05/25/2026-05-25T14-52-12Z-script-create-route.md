## User Prompt

commit 然后继续，直到所有完成

## Goals

- Move the basic script creation endpoint out of `scripts_legacy.py`.
- Keep episode ownership checks out of the new endpoint module's direct query
  surface.

## Changes

- Added `app.api.v1.endpoints.scripts_create` for `POST /scripts/`.
- Added `ScriptsRouteRepository.get_create_episode` for create-time episode
  ownership checks.
- Mounted the create router from `scripts_legacy.py` and removed the old create
  handler from the legacy file.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_create.py ai-pic-backend/app/repositories/scripts_route_repository.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified `POST /` is
    registered and `/generate` remains before `/{script_id}`.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_story_structure_sync.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_create.py ai-pic-backend/app/repositories/scripts_route_repository.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-52-12Z-script-create-route.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_create.py ai-pic-backend/app/repositories/scripts_route_repository.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-52-12Z-script-create-route.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Continue splitting `scripts_legacy.py`; synchronous generation and worker task
  processors remain in the legacy module.

## Linked Commits

Pending
