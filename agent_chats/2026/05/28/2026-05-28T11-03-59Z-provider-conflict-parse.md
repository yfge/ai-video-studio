---
id: "2026-05-28T11-03-59Z-provider-conflict-parse"
date: "2026-05-28T11:03:59Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - harness
  - provider-chain
related_paths:
  - scripts/harness/provider_chain_payloads.py
  - ai-pic-backend/tests/scripts/test_provider_chain_payloads.py
  - docs/exec-plans/active/commercial-script-quality.md
summary: Fail provider script parsing when scene conflict fields are missing.
---

## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Make provider-generated scripts fail early when scene-level conflict fields are absent.
- Require every provider scene parsed by `extract_structured_script()` to include nonblank `question`, `stakes`, `opposition`, and `turn`.
- Keep deeper commercial semantics in the existing deterministic scoring gates; this slice only closes the parser contract gap.

## Changes

- Added Task 40 and Task 41 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added `ai-pic-backend/tests/scripts/test_provider_chain_payloads.py` with parameterized red/green coverage for missing scene conflict fields.
- Updated `scripts/harness/provider_chain_payloads.py` so provider script parsing raises `script_scene_<n>_missing_<field>` before downstream media generation.

## Validation

- Red provider parser test:
  `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_payloads.py::test_extract_structured_script_requires_scene_conflict_fields -q`
  failed as expected: 4 failed because `extract_structured_script()` did not raise `ValueError` for blank `question`, `stakes`, `opposition`, or `turn`.
- Green provider parser and nearby provider-chain validation:
  `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_payloads.py tests/scripts/test_provider_chain_api.py tests/scripts/test_production_quality_regression.py -q`
  passed: 24 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 29 passed, 56 warnings.
- Focused provider harness validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_progression_score.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_payloads.py -q`
  passed: 32 passed, 27 warnings.
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

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence; this slice proves parser contract enforcement, not end-to-end generated script quality.
- Browser validation is not planned for this slice because it changes deterministic harness parsing and backend-adjacent tests, with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): validate provider scene conflicts`.
