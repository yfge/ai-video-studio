## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Make short-drama dialogue carry story information, not just be short.
- Reject filler-only dialogue such as `好的`, `嗯`, `知道了`, or `怎么会这样`.
- Keep product beat-contract quality gates and provider-chain structured scoring aligned.

## Changes

- Added Task 15 through Task 17 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added a product quality regression for filler-only beat dialogue.
- Added `dialogue_substance` issues in `beat_contract_specificity.py` and wired them into `beat_contract_quality.py`.
- Updated the short-drama beat prompt to require dialogue that advances clues, conflict, choices, threats, reversals, or concrete goals.
- Added a provider-chain regression for filler-only dialogue.
- Added `scripts/harness/production_dialogue_score.py` and wired it into provider-chain structured scoring.
- Updated the provider-chain script prompt to reject filler-only dialogue.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_filler_dialogue_lines -q`
  failed as expected because filler-only dialogue passed the existing gate.
- Green product quality test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 13 passed, 45 warnings.
- Red provider-chain test:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_filler_provider_dialogue -q`
  failed as expected because provider-chain structured scoring did not inspect dialogue substance yet.
- Green provider-chain regression:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 14 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 18 passed, 45 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 18 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Provider-backed generation and sample review remain the stronger evidence layer for end-to-end commercial quality.
- No browser run was needed in this slice because it only changes backend quality checks, prompt text, and harness scoring.

## Linked Commits

- Current commit: `feat(scripts): reject filler-only beat dialogue`.
