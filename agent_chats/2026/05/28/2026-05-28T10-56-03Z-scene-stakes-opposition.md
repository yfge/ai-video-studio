---
id: "2026-05-28T10-56-03Z-scene-stakes-opposition"
date: "2026-05-28T10:56:03Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - quality-gate
  - conflict
related_paths:
  - ai-pic-backend/app/services/script/beat_contract_conflict.py
  - scripts/harness/production_conflict_score.py
  - scripts/harness/provider_chain_payloads.py
  - docs/exec-plans/active/commercial-script-quality.md
summary: Require scene conflict stakes and opposition to name concrete losses and blocking sources.
---

## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Reject scenes whose conflict stakes are abstract pressure instead of concrete loss, deadline, money, customer, asset, file, proof, or permission risk.
- Reject scenes whose opposition is a vague situation instead of a concrete system, person, mechanism, file, log, permission, deletion, or blocking source.
- Align product beat-contract checks, provider structured score, provider fixtures, and prompts.

## Changes

- Added Task 38 and Task 39 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product and provider red/green tests for abstract `stakes` and `opposition`.
- Extended product `beat_contract_conflict.py` with `scene_conflict_stakes` and `scene_conflict_opposition` checks.
- Extended provider `production_conflict_score.py` with the same check ids.
- Added provider `stakes` and `opposition` fields to fixtures and the prompt schema.
- Updated product/provider prompt wording to require externally visible, concrete stakes and blocking sources.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py::test_quality_gate_rejects_abstract_scene_stakes_and_opposition -q`
  failed as expected: `assert True is False`, because abstract stakes/opposition still passed.
- Red provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_conflict_score.py::test_structured_score_rejects_abstract_provider_stakes_and_opposition -q`
  failed as expected: `assert True is False`, because provider conflict scoring still ignored stakes/opposition.
- Green product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py::test_quality_gate_rejects_abstract_scene_stakes_and_opposition -q`
  passed: 1 passed, 34 warnings.
- Green provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_conflict_score.py::test_structured_score_rejects_abstract_provider_stakes_and_opposition -q`
  passed: 1 passed, 26 warnings.
- Task 38 product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 21 passed, 48 warnings.
- Task 38 provider validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_conflict_score.py tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_api.py -q`
  passed: 22 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 29 passed, 56 warnings.
- Focused provider harness validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_progression_score.py tests/scripts/test_provider_chain_api.py -q`
  passed: 28 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_conflict.py scripts/harness/production_conflict_score.py ai-pic-backend/tests/unit/services/script/test_beat_contract_conflict_quality.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/provider_chain_fixtures.py scripts/harness/provider_chain_payloads.py`
  showed changed Python files under repository hard limits: 156, 127, 34, 51, 245, and 140 lines.
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

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence; this slice proves deterministic conflict-stakes specificity, not end-to-end generated script quality.
- Browser validation is not planned for this slice because it changes deterministic backend prompt/scoring helpers and harness tests, with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): require concrete scene stakes`.
