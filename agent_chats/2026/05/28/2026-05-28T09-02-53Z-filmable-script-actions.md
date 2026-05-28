## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Make beat-level scripts more directly filmable for commercial short-drama production.
- Reject internal-state or abstract-causality text in `visible_event` and action lines.
- Keep product quality gates and provider-chain structured scoring aligned.

## Changes

- Added Task 12 through Task 14 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added a product quality regression for internal-state `visible_event` and `action_lines`.
- Extended `beat_contract_specificity.py` to reject internal-state and abstract-change wording such as `意识到`, `感到`, `内心`, `命运`, and `关系变化`.
- Updated the short-drama beat prompt to require visible or audible screen behavior rather than psychological or abstract changes.
- Added a provider-chain regression for internal-state provider beats.
- Added `scripts/harness/production_filmability_score.py` and wired it into provider-chain structured scoring.
- Updated the provider-chain script prompt to forbid internal-state visible events and actions.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_internal_state_as_visible_action -q`
  failed as expected because internal-state wording passed the existing specificity gate.
- Green product quality test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 12 passed, 44 warnings.
- Red provider-chain test:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_internal_state_provider_beats -q`
  failed as expected because provider-chain structured scoring did not inspect event/action filmability yet.
- Green provider-chain regression:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 13 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 17 passed, 44 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 17 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Provider-backed generation remains the next stronger evidence layer for actual output quality once spend and provider state are approved.
- No browser run was needed in this slice because it only changes backend quality checks, prompt text, and harness scoring.

## Linked Commits

- Current commit: `feat(scripts): reject unfilmable beat actions`.
