## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama dramatic-purpose gate on top of beat structure and filmability.
- Reject scripts where `dramatic_purpose` is only a generic structure label such as `推进剧情`.
- Keep product quality gates and provider-chain structured scoring aligned without growing existing hotspot files past repository limits.

## Changes

- Added Task 20 and Task 21 to `docs/exec-plans/active/commercial-script-quality.md` for the dramatic-purpose slice.
- Added product and provider regression tests for `beat_dramatic_purpose_specificity`.
- Created `beat_contract_purpose.py` to keep product purpose checks out of the near-limit specificity module.
- Created `production_purpose_score.py` and wired it into provider-chain structured scoring.
- Updated product and provider script prompts to require concrete story turns, clues, choices, threats, or results in each beat purpose.
- Split the product purpose regression into a focused test file after diff contracts flagged `test_beat_contract_quality.py` as oversized at 258 lines.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_dramatic_purpose -q`
  failed as expected because the contract still passed without `beat_dramatic_purpose_specificity`.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_generic_provider_beat_purpose -q`
  failed as expected because provider structured scoring still passed without `beat_dramatic_purpose_specificity`.
- Green focused product tests:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 15 passed, 47 warnings.
- Green focused provider tests:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 16 passed, 27 warnings.
- Initial repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  failed: `test_beat_contract_quality.py` was oversized at 258 lines.
- Focused backend validation after splitting the test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 20 passed, 47 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 20 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts after splitting the test:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.
- Whitespace:
  `git diff --check`
  passed with no output.
- Targeted pre-commit:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`
  passed; `backend-pytest` was skipped for the documented local MySQL default issue.

## Next Steps

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.
- Browser validation was not run in this slice because the change is a deterministic backend prompt and quality-gate update with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): require concrete beat purposes`.
