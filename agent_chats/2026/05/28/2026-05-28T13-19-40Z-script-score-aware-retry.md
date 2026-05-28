## User Prompt

Continue working toward the active goal: 让剧本达到商用水准.

## Goals

- Improve the text-only script quality path after the 10-sample gate showed `script_quality_not_proven`.
- Convert retry attempts from random reruns into score-aware rewrites that use ScriptScore and structured-gate feedback.
- Preserve live evidence honestly: this slice improves scores but does not complete the commercial-quality goal.

## Changes

- Added focused regressions for opening `警告` hooks, `隐藏的修改者` opposition, prompt constraints, and screenplay rendering.
- Expanded structured gate markers to avoid false failures on those live expressions.
- Rendered all character labels and per-scene conflict metadata into provider-chain screenplay text before script scoring.
- Split script-only aggregate and feedback helpers into `production_script_quality_aggregate.py` to keep the runner under file-size limits.
- Fed script-score risks, rewrite guidance, structured failed checks, and lint issues into retry prompts.
- Tightened provider script prompts around ScriptScore pass dimensions, character distinction, visible protagonist-led actions, seeded hidden-code usage, opposition motives, permission/account rules, and non-terminal cliffhangers.
- Updated `commercial-script-quality.md` with Tasks 53-54.

## Validation

- Red/green targeted tests:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_hook_score.py::test_structured_score_accepts_opening_warning_as_immediate_threat tests/scripts/test_production_conflict_score.py::test_structured_score_accepts_hidden_modifier_as_concrete_opposition tests/scripts/test_provider_chain_script_prompt.py::test_build_script_prompt_aligns_with_script_score_pass_rubric tests/scripts/test_provider_chain_script_prompt.py::test_provider_chain_script_text_preserves_scene_conflict_metadata -q`
  - Failed before implementation with four expected failures, then passed after marker, prompt, and screenplay-rendering changes.
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_script_prompt.py::test_build_script_prompt_includes_repair_notes_for_retry tests/scripts/test_production_script_quality_regression.py::test_repair_notes_include_script_score_and_structured_feedback -q`
  - Failed before `repair_notes_from_sample` existed, then passed after score-aware retry feedback was added.
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_script_prompt.py::test_build_script_prompt_blocks_unseeded_backdoor_solutions tests/scripts/test_provider_chain_script_prompt.py::test_provider_chain_script_text_preserves_all_character_roles -q`
  - Failed before the prompt and screenplay included those constraints, then passed after implementation.
- Focused regression set:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py tests/scripts/test_provider_chain_script_prompt.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_api.py -q`
  - Passed after splitting prompt tests out of the oversized quality file: `38 passed, 27 warnings`.
- Live text probes:
  - `script-quality-live-text-3-score-rubric-20260528Tlocal`: verdict `script_quality_not_proven`, retry-adjusted passes 0/3, script score average 3.53.
  - `script-quality-live-text-3-repair-20260528Tlocal`: verdict `script_quality_not_proven`, retry-adjusted passes 0/3, script score average 3.80.
  - `script-quality-live-text-3-character-logic-20260528Tlocal`: verdict `script_quality_not_proven`, retry-adjusted passes 0/3, script score average 3.80.
  - `script-quality-live-text-3-motive-final-20260528Tlocal`: verdict `script_quality_not_proven`, retry-adjusted passes 1/3, script score average 3.97.
  - `script-quality-live-text-3-permission-seed-20260528Tlocal`: verdict `script_quality_not_proven`, retry-adjusted passes 0/3, script score average 3.75.
- Repository checks:
  - `python scripts/check_repo_docs.py`: `[check_repo_docs] ok`.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`: `[check_repo_contracts] ok (diff)`.
  - `git diff --check`: passed with no output.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`: passed all enabled hooks after an isort auto-fix was applied and the focused pytest/docs/contracts/diff/pre-commit checks were rerun; `pytest (backend quick gate)` was skipped because focused pytest covered this harness slice.

## Next Steps

- Do not claim the commercial-quality goal is complete.
- The best live run produced the first script-score pass, but stability is still below the 10-sample gate.
- Next quality work should target repeated structure, antagonist motivation depth, and permission/account causality before rerunning the 10-sample gate.

## Linked Commits

- Pending commit for this slice.
