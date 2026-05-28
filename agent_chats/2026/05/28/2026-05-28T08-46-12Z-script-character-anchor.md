## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Add a commercial short-drama character-anchor gate on top of beat structure and specificity.
- Reject scripts that use placeholder dialogue characters such as `主角` or rotate through unrelated named speakers without a recurring lead.
- Keep the implementation deterministic, schema-compatible, and within repository file-size contracts.

## Changes

- Added Task 5 and Task 6 to `docs/exec-plans/active/commercial-script-quality.md` for the character-anchor slice.
- Added tests for generic dialogue characters and missing recurring named character presence.
- Added `dialogue_character_specificity` and `scene_protagonist_presence` quality issues through `beat_contract_specificity.py`.
- Wired the beat-contract quality report to include the new character-anchor issues and updated `check_count` to 15.
- Updated the short-drama beat prompt to require stable named characters and a recurring scene lead across multiple beats.

## Validation

- Red test first:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_dialogue_characters tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_recurring_named_character_in_scene -q`
  failed as expected because the character-anchor check ids did not exist yet.
- Green focused quality test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 9 passed, 41 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 14 passed, 41 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Continue toward commercial-grade output by validating prompt behavior with provider-backed generated samples when spend and provider state are approved.
- Browser or provider-chain E2E was not run in this slice because the change is a deterministic backend prompt/quality-gate update with no API, frontend, media, or login surface change.

## Linked Commits

- Current commit: `feat(scripts): require character anchors in beat scripts`.
