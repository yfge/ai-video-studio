## User Prompt

PLEASE IMPLEMENT THIS PLAN: production-grade script generation pipeline from creative beats through scoring, auto rewrite, audio timeline, and storyboard placeholders.

## Goals

- Make async script generation default to a production pipeline.
- Keep synchronous generation as the lightweight standard path.
- Persist production audit metadata on Script and task agent runs.
- Add minimal frontend controls for production mode and automatic timeline/storyboard placeholder generation.

## Changes

- Added production orchestration helpers for hook schedule generation, ScriptScore-based rewrite attempts, best-attempt selection, storyboard hook/ad tag annotation, and optional auto timeline placeholder generation.
- Extended script generation request payloads with `generation_mode` and `auto_timeline_pipeline`.
- Wired async script generation to production mode by default while keeping sync generation standard.
- Updated the episode script generation form to expose the production async pipeline and automatic timeline/storyboard placeholder toggle.
- Added backend unit tests for hook schedule construction, rewrite selection, pass behavior, rewrite threshold enforcement, and storyboard hook/ad annotation.
- Added a harness smoke scenario for the episode script-generation form production controls.

## Validation

- Passed: `cd ai-pic-backend && PATH="$PWD/.venv/bin:$PATH" ./.venv/bin/python -m py_compile app/services/script/production_hooks.py app/services/script/production_scoring.py app/services/script/production_storyboard.py app/services/script/production_pipeline.py app/api/v1/endpoints/scripts_legacy.py app/api/v1/endpoints/scripts/generation.py run_tests.py`.
- Passed: `cd ai-pic-backend && PATH="$PWD/.venv/bin:$PATH" ./.venv/bin/pytest tests/unit/services/script/test_production_pipeline.py -v` (`6 passed`).
- Passed: `cd ai-pic-backend && PATH="$PWD/.venv/bin:$PATH" ./.venv/bin/pytest tests/unit/services/script/test_production_pipeline.py tests/scripts/test_script_dialogue_fallback.py tests/scripts/test_script_story_structure_sync.py tests/integration/test_task_pipeline_agent_run_audit.py -v` (`9 passed`).
- Passed: `cd ai-pic-frontend && npm run lint` (`0 errors`, existing warnings only).
- Passed: `cd ai-pic-frontend && npm run test` (`5 passed`).
- Passed on recheck: `cd ai-pic-frontend && npm run build` (Next.js production build completed).
- Passed: `python scripts/check_repo_docs.py`.
- Passed on recheck: `git diff --check`.
- Passed: focused contract diff for new services, frontend form split, harness scenario, `requirements.txt`, and `run_tests.py`.
- Backend quick gate: `cd ai-pic-backend && PATH="$PWD/.venv/bin:$PATH" ./.venv/bin/python run_tests.py quick` initially completed with `1930 passed`, `76 skipped`, `20 deselected`, and `4 failed`; focused rerun reduced this to 3 pre-existing/out-of-scope failures. Recheck completed with `1931 passed`, `76 skipped`, `20 deselected`, and the same 3 failures in story outline repair and AI-manager fallback expectations: `tests/unit/test_episode_step_outline_light.py::test_outline_missing_logline_triggers_repair`, `tests/unit/services/ai/test_scripts_ai_manager.py::test_call_ai_manager_script_passes_max_tokens_and_repairs_json`, and `tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_times_out_and_falls_back_to_direct`.
- Pre-commit: `pre-commit run --all-files` was attempted before commit. It did not pass because the all-files run touched unrelated historical files with EOF/Prettier fixes, ruff reported existing repository-wide lint violations, and the backend pytest hook used the non-venv Python 3.13 path and failed during import. The unrelated hook-generated working-tree edits were restored.
- Docker production build: `./docker/build_prod_images.sh` was attempted before commit. The initial multi-arch build hit a PyPI read timeout during backend dependency installation, then the script retried `linux/amd64`; the fallback backend image built successfully but final push to `registry.cn-beijing.aliyuncs.com/geyunfei/ai-video-backend:2f45b735` failed with `insufficient_scope: authorization failed`.
- Full changed-file contract check including `app/api/v1/endpoints/scripts_legacy.py` remains blocked by the existing legacy endpoint choke point: oversized file, oversized route handler, and historical direct SQLAlchemy `.query(...)` usage. The new production orchestration code was kept outside this legacy file and passes focused contract checks.
- Browser/harness: `python scripts/harness/doctor.py --run-id 2026-05-06T09-35-00Z-production-script-pipeline-browser --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:3001` passed. `browser_flow.py --scenario episode_script_generation_form_smoke` could not complete because Chrome DevTools timed out, Playwright Chrome aborted with `kill EPERM`, and Selenium could not create a Chrome session/cache in the sandbox. Evidence was recorded under `artifacts/runs/2026-05-06T09-35-00Z-production-script-pipeline-browser/`. Recheck with run id `2026-05-06T-recheck-production-script-pipeline` had the same browser-environment failure pattern after `doctor.py` passed.

## Next Steps

- Consider a separate cleanup/refactor of `scripts_legacy.py` to remove the historical contract violations from the active script route.
- Re-run the browser flow in an environment where Chrome DevTools or Playwright browser processes can be controlled.
- Triage the three remaining backend quick failures if they are still relevant to the current AI-manager/story-outline behavior.

## Linked Commits

- This commit: `feat(script): add production script generation pipeline`.
