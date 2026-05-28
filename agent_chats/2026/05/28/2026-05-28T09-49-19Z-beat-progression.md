## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama beat-progression gate on top of filmability and dramatic purpose.
- Reject scripts where multiple beats repeat the same screen state instead of moving the scene forward.
- Keep new tests in focused files so existing hotspot regression files stay under repository limits.

## Changes

- Added Task 22 and Task 23 to `docs/exec-plans/active/commercial-script-quality.md` for the beat-progression slice.
- Added product and provider regression tests for `beat_progression_repetition`.
- Created `beat_contract_progression.py` to detect duplicate beat screen states in a scene.
- Created `production_progression_score.py` and wired it into provider-chain structured scoring.
- Updated product and provider script prompts to require distinct screen states or new information for each beat.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_progression_quality.py::test_quality_gate_rejects_repeated_screen_beats -q`
  failed as expected because the contract still passed repeated screen beats.
- Red provider test:
  `pytest ai-pic-backend/tests/scripts/test_production_progression_score.py::test_structured_score_rejects_repeated_provider_screen_beats -q`
  failed as expected because provider structured scoring still passed repeated screen beats.
- Green product progression test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_progression_quality.py::test_quality_gate_rejects_repeated_screen_beats -q`
  passed: 1 passed, 33 warnings.
- Green provider progression test:
  `pytest ai-pic-backend/tests/scripts/test_production_progression_score.py::test_structured_score_rejects_repeated_provider_screen_beats -q`
  passed: 1 passed, 26 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 21 passed, 48 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 21 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_progression.py ai-pic-backend/tests/unit/services/script/test_beat_contract_progression_quality.py ai-pic-backend/tests/scripts/test_production_progression_score.py scripts/harness/production_structured_score.py scripts/harness/production_progression_score.py`
  showed `beat_contract_quality.py` at 249 lines, under the 250-line backend service hard limit.
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

- Current commit: `feat(scripts): reject repeated beat progression`.
