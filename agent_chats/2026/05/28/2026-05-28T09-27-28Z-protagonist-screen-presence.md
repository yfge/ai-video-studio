## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama screen-presence gate on top of dialogue character anchoring.
- Reject scripts where the recurring named protagonist only appears in dialogue metadata and never appears in beat-level visible action.
- Keep product quality gates and provider-chain structured scoring aligned.

## Changes

- Added Task 18 and Task 19 to `docs/exec-plans/active/commercial-script-quality.md` for the protagonist screen-presence slice.
- Added product and provider regression tests for `scene_protagonist_screen_presence`.
- Added `protagonist_screen_presence_issues()` to beat-contract specificity checks and wired it into the quality report.
- Updated provider-chain character scoring to require recurring speakers to appear in beat `visible_event` or `action` text.
- Updated product and provider script prompts to require visible protagonist action, movement, operation, or reaction.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_protagonist_in_screen_action -q`
  failed as expected because the contract still passed without `scene_protagonist_screen_presence`.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_provider_protagonist_in_screen_action -q`
  failed as expected because provider structured scoring still passed without `scene_protagonist_screen_presence`.
- Green focused product tests:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 14 passed, 46 warnings.
- Green focused provider tests:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 15 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 19 passed, 46 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 19 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
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

- Current commit: `feat(scripts): require protagonist screen presence`.
