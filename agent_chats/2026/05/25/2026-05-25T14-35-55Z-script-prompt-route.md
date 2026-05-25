## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue reducing `scripts_legacy.py` with a narrow prompt-preview route split.
- Keep prompt preview behavior registered before dynamic script record routes.

## Changes

- Added `app.api.v1.endpoints.scripts_prompt` for `/scripts/prompt/preview`.
- Added `ScriptsRouteRepository.get_prompt_preview_episode` so the new endpoint
  does not issue direct SQLAlchemy queries.
- Removed prompt preview handler and prompt template imports from
  `scripts_legacy.py`.
- Added a narrow API regression test for `/api/v1/scripts/prompt/preview` in a
  dedicated test file to avoid expanding the oversized legacy API test module.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_prompt.py ai-pic-backend/app/repositories/scripts_route_repository.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified
    `/prompt/preview`, `/generate`, and `/generate-async` register before
    `/{script_id}`.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_prompt_preview_api.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_prompt.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/scripts/test_script_prompt_preview_api.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-35-55Z-script-prompt-route.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_prompt.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/scripts/test_script_prompt_preview_api.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-35-55Z-script-prompt-route.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Continue splitting `scripts_legacy.py`; generation and regeneration task
  processors remain the largest legacy block.

## Linked Commits

Pending
