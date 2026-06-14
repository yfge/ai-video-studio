## User Prompt

PLEASE IMPLEMENT THIS PLAN:

Production Script Quality Hard Gate

Follow-up plan:

Production Script Prompt and LangGraph Upgrade

## Goals

- Tighten the default async production script-generation path behind `/scripts/generate-async`.
- Raise ScriptScore pass criteria to `overall_score >= 4.5` and every dimension `>= 4.2`.
- Try at most four production script versions total.
- Fail low-quality production tasks instead of persisting weak script drafts or starting auto timeline setup.
- Require beat-level `structured_script_contract` data for production async attempts.
- Upgrade the production-only short-drama prompt pack so quality is shaped before scoring, not only rejected after scoring.
- Thread `generation_mode=production` through LangGraph and direct AI-manager fallback paths.
- Refuse production legacy-shaped script payloads and mock fallback when no beat-level contract exists.

## Changes

- Added shared ScriptScore threshold constants in `app/services/script_score_thresholds.py`.
- Updated ScriptScore verdict computation and production scoring to use the shared strict thresholds.
- Changed production scoring to raise a script `NarrativeQualityGateError` after four low-quality attempts, with thresholds, selected attempt, attempt summaries, script scores, and rewrite guidance in the quality-gate details.
- Added `require_beat_contract` to script quality-gate evaluation/enforcement and wired async production attempts to require beat-contract payloads.
- Split `score_script_from_db` and beat-contract gate checks into focused helper modules to keep touched service files under repository file-size limits.
- Added unit coverage for strict thresholds, production hard failure, and required beat-contract behavior.
- Added production-mode propagation through `generate_script`, `ScriptLangGraphAgent.generate`, direct AI-manager script generation, and beat-contract prompt rendering.
- Upgraded production-only `script_scenes_short_drama` and `script_beats_short_drama` prompt sections with timestamp skeleton, close-up reaction, ScriptScore dimension mapping, and good/bad beat examples.
- Kept standard/default prompt behavior isolated from production-only hard brief text.
- Added generation-mode metadata to production-capable script outputs.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/test_narrative_quality_gate.py -q` -> red before implementation: old `4.0/3.5` thresholds still passed, production did not raise after low-quality attempts, and `require_beat_contract` was not accepted.
- `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/test_narrative_quality_gate.py -q` -> pass after implementation: `27 passed`.
- `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_script_quality_gate_beat_contract_requirement.py -q` -> pass after file-size cleanup and final verification: `41 passed`.
- `cd ai-pic-backend && python run_tests.py quick` -> blocked before tests during dependency install. Pip reported `ResolutionImpossible` because `pydantic==2.5.0` conflicts with `langchain-core==0.2.43` requiring `pydantic>=2.7.4` for this Python runtime.
- `python scripts/check_repo_docs.py` -> pass: `[check_repo_docs] ok`.
- `python scripts/check_repo_contracts.py --mode diff <backend and ledger changed files>` -> pass after splitting oversized touched files: `[check_repo_contracts] ok (diff)`.
- `git diff --check` -> pass after removing trailing blank lines.
- `cd ai-pic-backend && python - <<'PY' ... from app.services.scoring import ScriptScoreService, score_script_from_db ... PY` -> pass: moved scoring export imports cleanly.
- `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_propagates_generation_mode_to_langgraph_and_direct tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_standard_allows_legacy_direct_fallback -q` -> red before production legacy fallback guard: production accepted legacy-shaped direct fallback.
- `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_generation.py::test_production_beat_contract_prompt_contains_strict_score_gate tests/unit/services/script/test_beat_contract_generation.py::test_standard_beat_contract_prompt_omits_production_gate -q` -> red before prompt upgrade: production beat prompt lacked timestamp skeleton / close-up / examples.
- `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_propagates_generation_mode_to_langgraph_and_direct tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_standard_allows_legacy_direct_fallback -q` -> pass after production legacy fallback guard: `2 passed`.
- `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_generation.py::test_production_beat_contract_prompt_contains_strict_score_gate tests/unit/services/script/test_beat_contract_generation.py::test_standard_beat_contract_prompt_omits_production_gate -q` -> pass after prompt upgrade: `2 passed`.
- `cd ai-pic-backend && pytest tests/unit/test_story_format_prompt_templates.py::test_script_scenes_short_drama_production_prompt_has_quality_brief tests/unit/test_story_format_prompt_templates.py::test_script_scenes_short_drama_standard_prompt_omits_production_brief -q` -> pass: `2 passed`.
- `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/script/test_beat_contract_generation.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/test_script_quality_gate_beat_contract_requirement.py tests/unit/test_story_format_prompt_templates.py -q` -> pass: `28 passed`.
- `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_script_quality_gate_beat_contract_requirement.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/script/test_beat_contract_generation.py tests/unit/test_story_format_prompt_templates.py -q` -> pass after continuity helper split: `61 passed`.
- `cd ai-pic-backend && python -m py_compile app/services/ai/scripts.py app/services/ai/scripts_continuity.py app/services/ai/scripts_ai_manager.py app/services/script/beat_contract_generation.py app/services/script_agent.py` -> pass.
- `python scripts/check_repo_docs.py` -> pass after prompt/LangGraph changes: `[check_repo_docs] ok`.
- `python scripts/check_repo_contracts.py --mode diff <backend and ledger changed files>` -> pass after splitting `app/services/ai/scripts.py`: `[check_repo_contracts] ok (diff)`.
- `git diff --check` -> pass after prompt/LangGraph changes.
- `cd ai-pic-backend && python run_tests.py quick` -> still blocked before tests during dependency install by the same pinned dependency conflict: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43` requiring `pydantic>=2.7.4` on this Python runtime.
- Commit-prep `pre-commit run --all-files` -> failed on existing repository-wide issues and modified unrelated historical files. The automatic formatting side effects were restored outside this task scope. Failure signals included existing ruff violations in unrelated files, backend collection errors for historical harness exports such as `_BEAT_CONTRACT_MAX_TOKENS` / `structured_script_score`, and an `agent_chats` hook warning caused by the all-files formatter touching old ledger files. `frontend lint` passed inside the hook.
- After restoring unrelated pre-commit side effects and splitting `app/services/script/production_quality_gate.py`, reran focused validation:
  - `cd ai-pic-backend && pytest tests/unit/services/scoring/test_script_score_service.py tests/unit/services/script/test_production_pipeline.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/test_narrative_quality_gate.py tests/unit/services/test_script_quality_gate_beat_contract_requirement.py tests/unit/services/ai/test_scripts_generation_mixin.py tests/unit/services/script/test_beat_contract_generation.py tests/unit/test_story_format_prompt_templates.py -q` -> pass: `61 passed`.
  - `python -m py_compile ai-pic-backend/app/services/ai/scripts.py ai-pic-backend/app/services/ai/scripts_continuity.py ai-pic-backend/app/services/ai/scripts_ai_manager.py ai-pic-backend/app/services/script/beat_contract_generation.py ai-pic-backend/app/services/script/production_scoring.py ai-pic-backend/app/services/script/production_quality_gate.py ai-pic-backend/app/services/script_agent.py` -> pass.
  - `python scripts/check_repo_docs.py` -> pass: `[check_repo_docs] ok`.
  - `python scripts/check_repo_contracts.py --mode diff <backend and ledger changed files>` -> pass after extracting production quality-gate assembly: `[check_repo_contracts] ok (diff)`.
- `./docker/build_prod_images.sh` -> failed on dependency download/network integrity, not application compilation. Initial multi-arch build failed during backend `pip install` because the `jmespath-0.10.0` wheel download had hash mismatch (`expected d8988268...`, got empty-file sha `e3b0c442...`). Script fallback to `linux/amd64` then failed with `json.decoder.JSONDecodeError` while pip parsed package index content after repeated remote disconnect/read-timeout warnings.

2. Browser or MCP validation:

- Entry URL: not reached through Chrome DevTools MCP.
- User path: intended path was local async production script generation; Chrome DevTools MCP could not connect to Chrome.
- Console: unavailable because `list_pages` failed repeatedly with `Failed to fetch browser webSocket URL from http://127.0.0.1:9222/json/version: HTTP Not Found`.
- Network: unavailable for the same Chrome DevTools transport failure.
- Result: browser validation was not claimed. Fallback direct backend reproduction was run with `cd ai-pic-backend && python - <<'PY' ... PY`; final output printed `production_gate False production_script_score {'overall': 4.5, 'dimension': 4.2} [1, 2, 3, 4]`, `selected 4 4.4 ['仍未达到精品线']`, and `beat_contract_required True`.
- Prompt/LangGraph fallback reproduction was run with `cd ai-pic-backend && python - <<'PY' ... PY`; output printed `production_legacy_result None`, `agent_mode production`, `direct_mode production`, `production_prompt_gate True True True`, and `standard_prompt_gate False False`.
- Backend quick validation could not run because the helper tried to install dependencies and hit the pinned dependency conflict noted above.

3. Conflict signals and corrections:

- Initial assumption: threshold constants could live inside `app.services.scoring`.
- Contradicting evidence: production scoring only needs constants, and importing from the scoring package can execute broader scoring package imports.
- Reproduction and fix: moved thresholds to `app/services/script_score_thresholds.py` and reran focused tests.
- Final verified state: focused tests passed after the import cleanup.
- Initial assumption: Chrome DevTools browser validation could run against the local Docker stack.
- Contradicting evidence: Chrome DevTools MCP failed twice to connect to `127.0.0.1:9222`.
- Reproduction and fix: used the repo-approved fallback path and directly reproduced the backend production hard gate and required beat-contract behavior.
- Final verified state: no browser claim; fallback backend evidence recorded above.
- Initial assumption: hard quality gate alone was enough to address poor generated scripts.
- Contradicting evidence: production prompt and LangGraph/direct fallback could still produce or accept legacy-shaped output before scoring.
- Reproduction and fix: added production-only prompt tests and generation-mode propagation tests, then required production output to carry beat-level contract evidence.
- Final verified state: prompt and generation-mode tests passed, and standard/default prompt text remains isolated from production-only hard brief text.
- Initial assumption: repository-wide pre-commit would be a clean commit gate.
- Contradicting evidence: `pre-commit run --all-files` reformatted many unrelated historical files and exposed existing unrelated lint/import errors.
- Reproduction and fix: restored unrelated formatter side effects, kept the task-scoped files only, and reran focused tests plus repo docs/contracts.
- Final verified state: task-scoped validation passed; full all-files pre-commit remains blocked by existing unrelated repository issues.
- Initial assumption: production Docker images could be built before commit.
- Contradicting evidence: backend Docker `pip install` failed on PyPI download/hash and package-index JSON failures.
- Reproduction and fix: let `build_prod_images.sh` run through its built-in amd64 fallback; fallback also failed from package-index/network content errors.
- Final verified state: Docker build was attempted and failed before app compile steps due package download/index integrity errors.

## Next Steps

- Resolve or bypass the local `run_tests.py quick` dependency-install conflict if a full quick-suite pass is required in this Python runtime.
- Re-run Chrome DevTools browser validation after Chrome remote debugging is available on `127.0.0.1:9222`.

## Linked Commits

- Pending.
