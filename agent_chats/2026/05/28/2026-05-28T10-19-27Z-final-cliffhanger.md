## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama retention gate for final cliffhangers.
- Reject scripts where the final beat is labelled `cliffhanger` but the screen text fully resolves the story.
- Keep product and provider structured scoring aligned with the same failed check id.

## Changes

- Added Task 30 and Task 31 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product and provider regression tests for `cliffhanger_unresolved_threat`.
- Created `beat_contract_cliffhanger.py` for product cliffhanger specificity and unresolved-ending checks.
- Created `production_cliffhanger_score.py` and wired it into provider structured scoring.
- Updated product and provider prompts to forbid final beats that end with task completion, full recovery, all alarms off, or system restored.
- Reduced `beat_contract_quality.py` from 230 to 216 lines and `beat_contract_specificity.py` from 194 to 182 lines.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_cliffhanger_quality.py::test_quality_gate_rejects_resolved_final_cliffhanger -q`
  failed as expected because a resolved final beat labelled `cliffhanger` still passed.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py::test_structured_score_rejects_resolved_provider_final_cliffhanger -q`
  failed as expected because provider structured scoring still passed a resolved final beat labelled `cliffhanger`.
- Green product cliffhanger test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_cliffhanger_quality.py::test_quality_gate_rejects_resolved_final_cliffhanger -q`
  passed: 1 passed, 33 warnings.
- Green provider cliffhanger test:
  `pytest ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py::test_structured_score_rejects_resolved_provider_final_cliffhanger -q`
  passed: 1 passed, 26 warnings.
- Focused product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 15 passed, 47 warnings.
- Focused provider validation:
  `pytest ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 17 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_cliffhanger.py ai-pic-backend/app/services/script/beat_contract_specificity.py scripts/harness/production_cliffhanger_score.py scripts/harness/production_structured_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  showed changed Python files under repository hard limits.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 25 passed, 52 warnings.
- Focused provider harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 24 passed, 27 warnings.
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
  passed after isort normalized `beat_contract_quality.py`: merge-conflict, whitespace, yaml, ruff, black, isort, prettier, repo docs, repo contracts, and agent_chats ledger hooks passed; backend quick pytest was skipped for the documented local MySQL default issue; frontend lint had no files to check.

## Next Steps

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.
- Browser validation is not planned for this slice because it changes deterministic backend prompt and scoring helpers with no frontend, login, media-render, or API-surface change.
- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence when external provider state and spend are available.

## Linked Commits

- Current commit: `feat(scripts): reject resolved cliffhangers`.
