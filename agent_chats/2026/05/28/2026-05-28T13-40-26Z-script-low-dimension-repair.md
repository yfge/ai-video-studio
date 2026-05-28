## User Prompt

Continue the stepwise implementation toward improving script quality, then commit the current validated slice.

## Goals

- Make retry prompts react to specific low ScriptScore dimensions instead of only generic risks.
- Keep the change scoped to the evidence-backed improvement and avoid committing a prompt direction that live samples showed was worse.
- Preserve honest status: the commercial-quality goal is still not complete.

## Changes

- Added a regression assertion that repair notes include low ScriptScore dimensions below the per-dimension pass threshold.
- Added `_low_dimension_notes` to `production_script_quality_aggregate.py`, using `SCRIPT_SCORE_DIMENSION_PASS` to include only failing dimensions in retry feedback.
- Tested and rejected a causal story-spine prompt change after live samples regressed; that prompt change was reverted and is not part of this commit.

## Validation

- Red/green targeted tests:
  - `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_script_prompt.py::test_build_script_prompt_requires_causal_story_spine tests/scripts/test_production_script_quality_regression.py::test_repair_notes_include_script_score_and_structured_feedback -q`
  - Failed before implementation, then passed after adding causal-spine prompt text and low-dimension feedback.
- Focused regression set:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py tests/scripts/test_provider_chain_script_prompt.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_api.py -q`
  - Passed: `39 passed, 27 warnings`.
- Live text probe with causal spine:
  - `python scripts/harness/production_script_quality_regression.py --run-id script-quality-live-text-3-causal-spine-20260528Tlocal --api-url http://localhost:8010 --sample-count 3 --timeout-seconds 900`
  - Verdict `script_quality_not_proven`, retry-adjusted passes 0/3, script score average 3.77. This was worse than the prior best score-aware retry run, so the causal-spine prompt change was reverted.
- Sanity test after reverting causal spine:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py::test_repair_notes_include_script_score_and_structured_feedback tests/scripts/test_provider_chain_script_prompt.py -q`
  - Passed: `7 passed, 26 warnings`.
- Live text probe with only low-dimension feedback:
  - `python scripts/harness/production_script_quality_regression.py --run-id script-quality-live-text-3-low-dim-feedback-20260528Tlocal --api-url http://localhost:8010 --sample-count 3 --timeout-seconds 900`
  - Verdict `script_quality_not_proven`, retry-adjusted passes 1/3, script score average 4.00, script lint average 9.85, structured script average 3.84. One retry attempt failed JSON parsing, so this is progress but not a completion signal.

## Next Steps

- Do not claim the commercial-quality goal is complete.
- The next slice should reduce script JSON parse failures on retry attempts, likely by forwarding schema constraints through the text-generation route used by the provider-chain harness.
- After parse stability improves, rerun a larger script-quality gate before judging commercial readiness.

## Linked Commits

- Pending commit for this slice.
