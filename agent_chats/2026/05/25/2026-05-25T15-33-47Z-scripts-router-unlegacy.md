## User Prompt

commit 然后继续，直到所有完成

## Goals

- Continue the main-chain cleanup plan after the async generation processor split.
- Stop mounting the primary `/scripts` user routes through `scripts_legacy.py`.
- Keep old private helper imports available from `app.api.v1.endpoints.scripts`.

## Changes

- Rebuilt the main `/scripts` router in
  `app.api.v1.endpoints.scripts.__init__` by including the split catalog,
  prompt, generation, create, list, record, regeneration, quality, audio,
  timeline, and storyboard routers directly.
- Moved the no-trailing-slash `/api/v1/scripts` compatibility route into the
  package router.
- Re-exported compatibility task helpers from service-backed wrappers instead
  of importing them from `scripts_legacy.py`.
- Left `scripts_legacy.py` as a compatibility module for old direct imports
  only; `ai-pic-backend/app` no longer references it.
- Updated the task board and readiness plan to mark the legacy router main-path
  dependency as closed.

## Validation

1. Local checks:

- `cd ai-pic-backend && python -m py_compile app/api/v1/endpoints/scripts/__init__.py app/api/v1/endpoints/scripts_legacy.py tests/test_api.py` -> passed.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run tests/scripts/test_script_story_structure_sync.py tests/scripts/test_script_regeneration_soft_delete.py tests/test_api.py::TestScriptAPI -q` -> passed, 7 tests, warnings only.
- `cd ai-pic-backend && python - <<'PY' ... route assertion ... PY` -> passed; required `/scripts`, `/scripts/`, `/scripts/generate`, `/scripts/generate-async`, and `/scripts/{script_id}/export` routes are present. Import emitted the existing MiniMax voice preload warning because no API secret is configured locally, but the route assertion succeeded.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check` -> passed.
- `pre-commit run --files <changed files>` -> first run reformatted `scripts/__init__.py` with black/isort, then backend quick gate passed.
- `pre-commit run --files <changed files>` -> passed after formatting, including backend quick gate; frontend lint skipped because no frontend files were changed.

2. Browser or MCP validation:

- Not run. This slice changes backend router assembly and import surfaces; it does not change frontend controls or browser-visible UI.

3. Conflict signals and corrections:

- Initial route assertion used a list in a set and failed with `TypeError: unhashable type: 'list'`.
- The assertion was corrected to compare tupled method lists and then passed.

## Next Steps

- Run repo docs, contract, diff, and pre-commit gates.
- Commit this router dependency removal as its own atomic change.
- Continue to the remaining production proof work: 10 narrow 2D/3D cartoon samples and metric capture.

## Linked Commits

Pending
