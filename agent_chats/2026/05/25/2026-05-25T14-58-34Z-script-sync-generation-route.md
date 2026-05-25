## User Prompt

commit 然后继续，直到所有完成

## Goals

- Move synchronous `/scripts/generate` out of `scripts_legacy.py`.
- Keep the new endpoint thin, keep direct SQLAlchemy query access behind
  repositories, and stay within service file-size limits.

## Changes

- Added `app.api.v1.endpoints.scripts_generation_sync` as the thin synchronous
  generation endpoint.
- Added `app.services.script.sync_generation` for the synchronous script
  generation workflow and `sync_generation_payloads` for parsing/model/metadata
  helpers.
- Added `ScriptsRouteRepository.get_generation_episode` for generation-time
  episode ownership checks.
- Updated the mock AI fixture to patch the new generation service import.
- Removed the old synchronous generation route and now-unused imports from
  `scripts_legacy.py`.
- Updated `tasks.md` and the active commercial readiness plan.

## Validation

- `python -m py_compile ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_sync.py ai-pic-backend/app/services/script/sync_generation.py ai-pic-backend/app/services/script/sync_generation_payloads.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py`
  - Passed.
- `cd ai-pic-backend && python - <<'PY' ...`
  - Passed: imported `scripts_legacy.router` and verified `/generate` remains
    registered before `/{script_id}`.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI tests/scripts/test_script_story_structure_sync.py -q`
  - Passed: 5 tests.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_sync.py ai-pic-backend/app/services/script/sync_generation.py ai-pic-backend/app/services/script/sync_generation_payloads.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-58-34Z-script-sync-generation-route.md`
  - Passed.
- `git diff --check`
  - Passed.
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py ai-pic-backend/app/api/v1/endpoints/scripts_generation_sync.py ai-pic-backend/app/services/script/sync_generation.py ai-pic-backend/app/services/script/sync_generation_payloads.py ai-pic-backend/app/repositories/scripts_route_repository.py ai-pic-backend/tests/fixtures/mock_ai_service.py tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md agent_chats/2026/05/25/2026-05-25T14-58-34Z-script-sync-generation-route.md`
  - Passed, including repository checks and backend quick gate.

## Next Steps

- Continue splitting `scripts_legacy.py`; async generation and regeneration
  worker processors remain the largest legacy block.

## Linked Commits

Pending
