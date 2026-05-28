## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama scene-structure gate for dramatic question and scene turn.
- Reject product beat contracts and provider-chain scripts where a scene has only generic progression wording instead of a concrete question or turn.
- Keep the backend quality service under file-size limits by moving scene-conflict checks into a focused helper.

## Changes

- Added Task 28 and Task 29 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product and provider regression tests for `scene_conflict_question` and `scene_conflict_turn`.
- Created `beat_contract_conflict.py` for product scene-conflict quality checks.
- Created `production_conflict_score.py` and wired it into provider structured scoring.
- Updated product and provider prompts so generated scenes must include a concrete question and turn.
- Updated provider-chain fixtures with concrete `question` and `turn` fields and unique dialogue lines.
- Reduced `beat_contract_quality.py` from 249 to 230 lines and `beat_contract_specificity.py` from 200 to 194 lines.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py::test_quality_gate_requires_scene_question_and_turn -q`
  failed as expected because the quality report still passed an empty `conflict.question` and generic `conflict.turn`.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_conflict_score.py::test_structured_score_requires_provider_scene_question_and_turn -q`
  failed as expected after neutralizing unrelated repeated dialogue in the test payload because provider structured scoring still passed generic or missing question/turn data.
- Green product conflict test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py::test_quality_gate_requires_scene_question_and_turn -q`
  passed: 1 passed, 33 warnings.
- Green provider conflict test:
  `pytest ai-pic-backend/tests/scripts/test_production_conflict_score.py::test_structured_score_requires_provider_scene_question_and_turn -q`
  passed: 1 passed, 26 warnings.
- Focused product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 15 passed, 47 warnings.
- Focused provider validation:
  `pytest ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 17 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_conflict.py ai-pic-backend/app/services/script/beat_contract_specificity.py scripts/harness/production_conflict_score.py scripts/harness/production_structured_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  showed changed Python files under repository hard limits.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 24 passed, 51 warnings.
- Focused provider harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 23 passed, 27 warnings.
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
  passed: merge-conflict, whitespace, yaml, ruff, black, isort, prettier, repo docs, repo contracts, and agent_chats ledger hooks passed; backend quick pytest was skipped for the documented local MySQL default issue; frontend lint had no files to check.

## Next Steps

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.
- Browser validation is not planned for this slice because it changes deterministic backend prompt/scoring helpers and test fixtures, with no frontend, login, media-render, or API-surface change.
- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.

## Linked Commits

- Current commit: `feat(scripts): require scene question turns`.
