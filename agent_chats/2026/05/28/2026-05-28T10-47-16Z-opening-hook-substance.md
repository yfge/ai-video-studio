---
id: "2026-05-28T10-47-16Z-opening-hook-substance"
date: "2026-05-28T10:47:16Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - quality-gate
  - opening-hook
related_paths:
  - ai-pic-backend/app/services/script/beat_contract_hook.py
  - scripts/harness/production_hook_score.py
  - ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt
  - docs/exec-plans/active/commercial-script-quality.md
summary: Require scene 1 beat 1 to show an immediate visible hook, not only a hook label and short duration.
---

## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Reject scripts where scene 1 beat 1 is labelled `hook` and short enough, but only shows ordinary arrival or setup.
- Keep product beat-contract scoring and provider structured scoring aligned on `opening_hook_substance`.
- Update prompts so model output puts the concrete hook on screen in the first beat.

## Changes

- Added Task 36 and Task 37 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product and provider regression tests for neutral arrival-style opening hooks.
- Created `beat_contract_hook.py` to keep hook-substance checks separate from duration checks.
- Created `production_hook_score.py` and wired it into provider structured scoring.
- Updated product and provider prompts to require the first beat to show an anomaly, loss, countdown, threat, evidence, reversal, or urgent question.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py::test_quality_gate_rejects_opening_hook_without_immediate_threat -q`
  failed as expected: `assert True is False`, because ordinary arrival text still passed.
- Red provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_hook_score.py::test_structured_score_rejects_provider_opening_hook_without_immediate_threat -q`
  failed as expected: `assert True is False`, because provider structured scoring still passed ordinary arrival text.
- Green product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py::test_quality_gate_rejects_opening_hook_without_immediate_threat -q`
  passed: 1 passed, 34 warnings.
- Green provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_hook_score.py::test_structured_score_rejects_provider_opening_hook_without_immediate_threat -q`
  passed: 1 passed, 26 warnings.
- Task 36 product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 21 passed, 48 warnings.
- Task 36 provider validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_hook_score.py tests/scripts/test_production_quality_regression.py -q`
  passed: 18 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 28 passed, 55 warnings.
- Focused provider harness validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_progression_score.py tests/scripts/test_provider_chain_api.py -q`
  passed: 27 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_hook.py scripts/harness/production_hook_score.py ai-pic-backend/app/services/script/beat_contract_quality.py scripts/harness/production_structured_score.py ai-pic-backend/tests/unit/services/script/test_beat_contract_hook_quality.py ai-pic-backend/tests/scripts/test_production_hook_score.py scripts/harness/provider_chain_payloads.py`
  showed changed Python files under repository hard limits: 71, 73, 218, 172, 36, 46, and 136 lines.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.
- Whitespace:
  `git diff --check`
  passed with no output.
- Format correction:
  an intermediate pre-commit run reformatted the two hook test files with black; after formatting, `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_hook_quality.py tests/scripts/test_production_hook_score.py -q` passed: 4 passed, 34 warnings.
- Targeted pre-commit:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`
  passed: merge-conflict, whitespace, yaml, ruff, black, isort, prettier, repo docs, repo contracts, and agent_chats ledger hooks passed; backend quick pytest was skipped for the documented local MySQL default issue; frontend lint had no files to check.

## Next Steps

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence; this slice proves deterministic opening-hook substance, not end-to-end generated script quality.
- Browser validation is not planned for this slice because it changes deterministic backend prompt/scoring helpers and harness tests, with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): require immediate opening hooks`.
