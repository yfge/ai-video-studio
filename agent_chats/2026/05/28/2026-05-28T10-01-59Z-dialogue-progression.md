## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama dialogue progression gate.
- Reject scripts where beat dialogue repeats the same non-filler line across a scene.
- Move product dialogue checks out of the crowded specificity helper so future quality work has safer file-size headroom.

## Changes

- Added Task 26 and Task 27 to `docs/exec-plans/active/commercial-script-quality.md` for the dialogue-progression slice.
- Added product and provider regression tests for `dialogue_progression_repetition`.
- Created `beat_contract_dialogue.py` for product dialogue substance and repeated-line checks.
- Removed dialogue-substance logic from `beat_contract_specificity.py`, reducing that file from 238 to 200 lines.
- Extended provider-chain dialogue scoring with repeated-line detection.
- Updated product and provider script prompts to forbid repeating the same dialogue line within one scene.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py::test_quality_gate_rejects_repeated_dialogue_lines -q`
  failed as expected because repeated non-filler dialogue still passed.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_dialogue_score.py::test_structured_score_rejects_repeated_provider_dialogue_lines -q`
  failed as expected because provider structured scoring still passed repeated non-filler dialogue.
- Green product dialogue test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py::test_quality_gate_rejects_repeated_dialogue_lines -q`
  passed: 1 passed, 33 warnings.
- Green provider dialogue test:
  `pytest ai-pic-backend/tests/scripts/test_production_dialogue_score.py::test_structured_score_rejects_repeated_provider_dialogue_lines -q`
  passed: 1 passed, 26 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 23 passed, 50 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 22 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_dialogue.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/tests/unit/services/script/test_beat_contract_dialogue_quality.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py scripts/harness/production_dialogue_score.py`
  showed changed files under repository hard limits.
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
- Browser validation was not run in this slice because the change is a deterministic backend prompt and quality-gate update with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): reject repeated dialogue beats`.
