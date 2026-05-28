## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add production-grade duration mapping to beat-level script contracts.
- Reject scripts whose beat durations are missing or cannot map to scene duration.
- Keep product quality gates and provider-chain structured scoring aligned.

## Changes

- Added Task 9 through Task 11 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product quality tests for missing beat durations and scene duration mismatch.
- Added `beat_contract_duration.py` and wired `beat_duration_required` / `scene_duration_alignment` into the beat-contract quality report.
- Updated the short-drama beat prompt to require positive beat durations whose sum matches scene duration.
- Added provider-chain duration tests and valid fixture beat durations.
- Added `scripts/harness/production_duration_score.py` and merged duration failures into provider-chain `structured_script_score`.
- Updated provider-chain script prompt to require beat duration sums.

## Validation

- Red product tests:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_beat_durations_for_timed_scene tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_scene_duration_mismatch -q`
  failed as expected because duration checks did not exist yet.
- Green product quality test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 11 passed, 43 warnings.
- Red provider-chain tests:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_provider_beat_durations ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_provider_scene_duration_mismatch -q`
  failed as expected because provider-chain duration checks did not exist yet.
- Green provider-chain regression:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 12 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 16 passed, 43 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 16 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Provider-backed generation remains the next stronger evidence layer for actual output quality once spend and provider state are approved.
- This slice did not run browser validation because it changes backend quality checks, prompt text, and harness scoring only.

## Linked Commits

- Current commit: `feat(scripts): enforce beat duration budgets`.
