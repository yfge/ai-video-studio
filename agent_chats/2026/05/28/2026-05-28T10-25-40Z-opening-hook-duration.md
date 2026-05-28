## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama pace gate for the opening hook.
- Reject scripts where scene 1 beat 1 is labelled `hook` but takes more than 3 seconds to land.
- Keep product and provider duration scoring aligned with the same failed check id.

## Changes

- Added Task 32 and Task 33 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product and provider regression tests for `opening_hook_duration`.
- Extended product `beat_contract_duration.py` and provider `production_duration_score.py` to reject scene 1 beat 1 durations above 3 seconds.
- Updated product and provider valid fixtures so scene 1 lands the hook in 3 seconds while preserving 15-second scene totals.
- Updated product and provider prompts to require the first hook beat within 3 seconds.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py::test_quality_gate_rejects_slow_opening_hook -q`
  failed as expected because a 5-second opening hook still passed.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_hook_score.py::test_structured_score_rejects_slow_provider_opening_hook -q`
  failed as expected because provider structured scoring still passed a 5-second opening hook.
- Green product hook test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py::test_quality_gate_rejects_slow_opening_hook -q`
  passed: 1 passed, 33 warnings.
- Green provider hook test:
  `pytest ai-pic-backend/tests/scripts/test_production_hook_score.py::test_structured_score_rejects_slow_provider_opening_hook -q`
  passed: 1 passed, 26 warnings.
- Focused product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 20 passed, 47 warnings.
- Focused provider validation:
  `pytest ai-pic-backend/tests/scripts/test_production_hook_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 17 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_duration.py scripts/harness/production_duration_score.py ai-pic-backend/tests/scripts/provider_chain_fixtures.py ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  showed changed Python files under repository hard limits.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 26 passed, 53 warnings.
- Focused provider harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_hook_score.py ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 25 passed, 27 warnings.
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
- Browser validation is not planned for this slice because it changes deterministic backend prompt and scoring helpers with no frontend, login, media-render, or API-surface change.
- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.

## Linked Commits

- Current commit: `feat(scripts): enforce three second hooks`.
