## User Prompt

commit

## Goals

- Commit the provider-quality evidence slice for the commercial script quality plan.
- Repair stale backend tests so full pytest reflects current Timeline and script regeneration boundaries.
- Harden provider-chain quality probes around terminal-failure cliffhangers and dialogue-source repetition.

## Changes

- Updated the Timeline pipeline import test to patch `generate_timeline_shot_plan_from_current_version`, which is the current endpoint boundary.
- Completed the provider-chain structured-script fixture with current required scene fields and beats.
- Patched script regeneration queue enqueueing in the story-structure sync test to avoid executing a local Celery task against the default MySQL connection.
- Made provider-chain screenplay lint text use the final beat for `【悬念】` instead of repeating the final scene plot.
- Rejected terminal-failure endings such as `数据丢失`, `进度条到100%`, and `来不及了` as unresolved cliffhangers.
- Clarified provider prompt rules for live cliffhangers and unique dialogue.
- Adjusted dialogue repetition scoring to check scene-level video dialogue source separately from beat-level dialogue, while still rejecting repeated beat dialogue within a scene.
- Recorded Task 46-48 progress in `docs/exec-plans/active/commercial-script-quality.md`.

## Validation

- Red reproduction:
  - `cd ai-pic-backend && pytest tests/integration/test_timeline_pipeline_import_api.py::test_process_timeline_pipeline_imports_audio_timeline_to_timeline_spec tests/scripts/test_provider_chain_regression.py::test_extract_structured_script_requires_dialogue tests/scripts/test_script_story_structure_sync.py::test_generate_script_syncs_normalized_scenes -q`
  - Observed 3 failures from stale test boundaries and eager regeneration queue execution.
- Focused test repair:
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_regression.py tests/integration/test_timeline_pipeline_import_api.py tests/scripts/test_script_story_structure_sync.py -q`
  - Passed: `7 passed`.
- Provider-chain smoke:
  - `python scripts/harness/provider_chain_regression.py --mode smoke --run-id quality-smoke-worktree-commercial-20260528Tlocal --api-url http://localhost:8010 --episode-id 133 --script-id 117 --timeout-seconds 900 --poll-interval-seconds 5 --video-concurrency 1`
  - Passed with DeepSeek script generation, Timeline creation and shot plan, MiniMax TTS, OpenAI image generation, Seedance video generation, and final render probe.
  - Evidence: `artifacts/runs/quality-smoke-worktree-commercial-20260528Tlocal/provider_chain.json`.
- Quality audit:
  - `python scripts/harness/production_quality_regression.py --mode audit-existing --run-id quality-audit-worktree-commercial-20260528Tlocal --input-run artifacts/runs/quality-smoke-worktree-commercial-20260528Tlocal/provider_chain.json`
  - Verdict: `not_trial_ready`; this exposed the terminal-failure cliffhanger issue in the smoke output.
- TDD red/green:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_quality_regression.py::test_build_script_prompt_accepts_optional_premise -q`
  - Red before implementation, then passed after the cliffhanger tests were split into the focused file: `4 passed`.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py::test_dialogue_score_allows_scene_dialogue_source_to_mirror_unique_beats -q`
  - Red before implementation, then `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py -q` passed: `3 passed`.
- Live text probe:
  - `artifacts/runs/quality-text-probe-dialogue-v2-20260528Tlocal/text_probe.json`
  - DeepSeek `deepseek-v4-flash` returned `structured_passed=true`, `failed_checks=[]`, average `3.84`, and final cliffhanger tag `未知操作者`.
- Final targeted backend validation:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_payloads.py tests/scripts/test_provider_chain_regression.py tests/integration/test_timeline_pipeline_import_api.py tests/scripts/test_script_story_structure_sync.py -q`
  - Passed before the cliffhanger-test split: `32 passed, 62 warnings`.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_payloads.py tests/scripts/test_provider_chain_regression.py tests/integration/test_timeline_pipeline_import_api.py tests/scripts/test_script_story_structure_sync.py -q`
  - Passed after the cliffhanger-test split: `33 passed, 62 warnings`.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_quality_regression.py::test_build_script_prompt_accepts_optional_premise -q`
  - Passed after the test split: `4 passed, 26 warnings`.
  - `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_cliffhanger_score.py -q`
  - Passed after pre-commit formatting: `6 passed, 26 warnings`.
- Full backend validation:
  - `cd ai-pic-backend && pytest`
  - Passed before the cliffhanger-test split: `2145 passed, 94 skipped, 2108 warnings in 86.85s`.
  - Passed again after the cliffhanger-test split: `2145 passed, 94 skipped, 2108 warnings in 86.14s`.
- Repository checks:
  - `python scripts/check_repo_docs.py`: `[check_repo_docs] ok`.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`: `[check_repo_contracts] ok (diff)`.
  - `git diff --check`: passed with no output.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`: passed after `black` and `isort` reformatted `test_production_dialogue_score.py`; final rerun passed all enabled hooks, with `pytest (backend quick gate)` skipped because full backend pytest was run separately.

## Next Steps

- This slice improves live provider script quality evidence but does not close the full commercial-readiness objective. Remaining proof still needs sample-scale provider/browser runs and full production-quality pass criteria beyond a one-scene smoke/text probe.

## Linked Commits

- Pending commit for this slice.
