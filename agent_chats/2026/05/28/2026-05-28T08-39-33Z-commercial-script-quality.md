## User Prompt

commit

## Goals

- Continue moving generated scripts toward commercial short-drama quality.
- Reject beat contracts that satisfy structure but use vague conflict, abstract actions, symbolic payoff, or empty cliffhanger.
- Keep the new rules aligned with existing repository docs, file-size limits, and quality-gate wiring.

## Changes

- Added an active execution plan at `docs/exec-plans/active/commercial-script-quality.md` and registered it in `docs/README.md`.
- Added quality-gate regression tests for generic conflict/abstract beats and symbolic payoff/empty cliffhanger.
- Added deterministic commercial-specificity helpers in `beat_contract_specificity.py`.
- Wired the beat-contract quality gate to emit `scene_conflict_specificity`, `beat_visible_event_specificity`, `beat_action_specificity`, `payoff_specificity`, and `cliffhanger_specificity`.
- Updated the short-drama beat prompt to require concrete stakes, opposition, screen-visible events, concrete payoff, and concrete cliffhanger threats.

## Validation

- Red test first:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_conflict_and_abstract_beats tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_symbolic_payoff_and_empty_cliffhanger -q`
  failed as expected because the commercial-specificity check ids did not exist yet.
- Green focused quality test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q`
  passed: 7 passed, 39 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 12 passed, 39 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.

## Next Steps

- Run provider-backed generation and browser evidence only after provider account state and spend scope are confirmed.
- The earlier production image build was not rerun in this slice because it pushes images by default and this was not a release request.

## Linked Commits

- Current commit: `feat(scripts): tighten commercial beat quality`.
