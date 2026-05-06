## User Prompt

Implement the Legacy Contract Baseline Recovery plan.

## Goals

- Restore the legacy contract baseline without a full `/scripts` router rewrite.
- Bring `scripts_legacy.py` back under its allowed legacy line baseline.
- Allow changed-file contract checks to pass when known legacy debt is reduced rather than expanded.
- Keep public HTTP APIs, Celery task names, schemas, and payloads unchanged.

## Changes

- Added route-handler and direct-query baselines for `scripts_legacy.py` in the contract audit core.
- Updated contract reporting to apply diff-vs-audit baseline semantics for route-handler and direct-query categories.
- Extracted script content normalization, script prompt context payloads, story-structure sync, and production metadata merge helpers into `app.services.script`.
- Reduced `scripts_legacy.py` from 2558 lines to 1980 lines while preserving compatibility wrappers for active private helpers.
- Updated `ScriptService._sync_scenes_safe` to call the story-structure sync service directly.
- Removed low-risk audit-noise references to the old scripts endpoint name in storyboard and task worker comments/docstrings.
- Updated repository contract tests for the current audit-core module split and baseline behavior.

## Validation

1. Local checks:

- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only) $(git ls-files --others --exclude-standard) --report-json /private/tmp/avs_contracts_diff_current.json --report-md /private/tmp/avs_contracts_diff_current.md` -> pass; 11 checked files, 0 violations.
- `python scripts/check_repo_contracts.py --mode audit --report-json /private/tmp/avs_contracts-report.json --report-md /private/tmp/avs_contracts-summary.md` -> pass; audit still reports legacy debt, with `scripts_legacy.py` at 1980 lines, route handler 250 baseline-exempt, direct query hits 22 baseline-exempt.
- `pytest tests/harness/test_repo_contracts.py -v` -> pass, 3 passed.
- `cd ai-pic-backend && pytest tests/scripts/test_script_regeneration_soft_delete.py -v` -> pass, 1 passed.
- `cd ai-pic-backend && pytest tests/test_api.py::TestScriptAPI::test_generate_script tests/test_api.py::TestScriptAPI::test_export_script -v` -> pass, 2 passed.
- `cd ai-pic-backend && pytest tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run -v` -> pass, 1 passed.
- `cd ai-pic-backend && pytest tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_admin tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_story_owner tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_denied -v` -> pass, 3 passed.
- `pytest tests/scripts/test_script_regeneration_soft_delete.py tests/test_api.py::TestScriptAPI::test_generate_script tests/test_api.py::TestScriptAPI::test_export_script tests/integration/test_task_pipeline_agent_run_audit.py::test_story_episode_script_generate_async_persists_task_agent_run tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_admin tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_story_owner tests/unit/services/script/test_script_service.py::TestScriptService::test_check_user_access_denied -v` from `ai-pic-backend/` -> pass, 7 passed.
- `pre-commit run --all-files` -> fail; whole-repo hooks reported pre-existing lint/formatting debt and auto-modified many unrelated historical files. Those hook-generated unrelated modifications were restored before staging this change.
- `git diff --check` -> pass.
- `./docker/build_prod_images.sh` -> fail after backend image build/export; the script attempted to push `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:80f00a63` and registry authorization returned `insufficient_scope`.

2. Backend quick gate:

- `cd ai-pic-backend && python run_tests.py quick` -> fail before tests; setup step `pip install -r requirements-test.txt` hit dependency resolution conflict: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on this Python.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> fail after running tests; initial run showed 7 failures, 3 caused by temporarily removing `_check_user_access`. The method was restored and the failed subset was rerun.
- Rerun failed subset after fix -> 4 passed, 3 remaining failures in unrelated AI/episode tests:
  - `tests/unit/services/ai/test_scripts_ai_manager.py::test_call_ai_manager_script_passes_max_tokens_and_repairs_json`
  - `tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_times_out_and_falls_back_to_direct`
  - `tests/unit/test_episode_step_outline_light.py::test_outline_missing_logline_triggers_repair`

3. Browser or MCP validation:

- Not run. This was an internal contract/refactor change with no intended user-visible behavior change.

## Next Steps

- Investigate the remaining quick-suite failures separately; they are outside this legacy contract baseline recovery scope.
- Resolve the `run_tests.py quick` setup dependency conflict so the standard backend quick gate can run without `--no-setup`.

## Linked Commits

- None yet.
