## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Align provider-chain structured scoring with the product beat-contract character-anchor gate.
- Reject provider-chain script payloads that use generic speakers or fail to keep a recurring named scene lead.
- Keep provider-chain prompt requirements consistent with the deterministic harness checks.

## Changes

- Added Task 7 and Task 8 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added provider-chain regression tests for generic `speaker` names and missing recurring named speakers.
- Added `scripts/harness/production_character_score.py` for dictionary-based scene and beat speaker checks.
- Wired `structured_script_score` to include `dialogue_character_specificity` and `scene_protagonist_presence` failures.
- Updated the provider-chain script prompt to forbid generic speaker names and require reuse of the named protagonist in scene and beat dialogue.

## Validation

- Red test first:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_generic_provider_dialogue_speakers ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_recurring_provider_scene_speaker -q`
  failed as expected because provider-chain structured scoring did not emit character-anchor failed checks yet.
- Green provider-chain regression:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`
  passed: 10 passed, 27 warnings.
- Focused harness validation:
  `pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q`
  passed: 14 passed, 27 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Provider-backed sample generation remains the next stronger evidence layer once provider spend and account state are approved.
- No browser run was needed in this slice because it only changes provider-chain harness scoring and prompt text.

## Linked Commits

- Current commit: `feat(harness): score provider script character anchors`.
