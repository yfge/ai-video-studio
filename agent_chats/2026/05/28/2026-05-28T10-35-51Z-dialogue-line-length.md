---
id: "2026-05-28T10-35-51Z-dialogue-line-length"
date: "2026-05-28T10:35:51Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - quality-gate
  - dialogue
related_paths:
  - ai-pic-backend/app/services/script/beat_contract_quality.py
  - scripts/harness/production_dialogue_score.py
  - ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt
  - docs/exec-plans/active/commercial-script-quality.md
summary: Enforce 15-visible-character dialogue lines in product and provider script quality gates.
---

## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Make the product beat-contract gate enforce the same 15-visible-character dialogue limit requested in provider prompts.
- Reject provider-chain structured script samples with slow, overlong dialogue as a hard failure, not only a lower score.
- Keep product prompt, deterministic quality gate, and provider harness scoring aligned on `dialogue_line_length`.

## Changes

- Added Task 34 and Task 35 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added product regression coverage for a dialogue line over 15 visible characters.
- Added provider structured-score regression coverage for the same overlong dialogue failure.
- Changed `evaluate_beat_contract_quality` default dialogue limit from 24 to 15 visible characters.
- Extended provider dialogue scoring to emit `dialogue_line_length` when any scene or beat dialogue exceeds 15 visible characters.
- Updated the beat-contract prompt to require dialogue lines no longer than 15 visible characters.

## Validation

- Red product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py::test_quality_gate_rejects_long_dialogue_line -q`
  failed as expected: `assert True is False`, because the product gate still allowed the long line.
- Red provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py::test_structured_score_rejects_long_provider_dialogue_line -q`
  failed as expected: `assert True is False`, because provider structured scoring still passed the long line.
- Green product test:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py::test_quality_gate_rejects_long_dialogue_line -q`
  passed: 1 passed, 34 warnings.
- Green provider test:
  `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py::test_structured_score_rejects_long_provider_dialogue_line -q`
  passed: 1 passed, 26 warnings.
- Task 34 product validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 21 passed, 48 warnings.
- Task 34 provider validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_quality_regression.py -q`
  passed: 18 passed, 27 warnings.
- Focused backend validation:
  `cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_hook_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q`
  passed: 27 passed, 54 warnings.
- Focused provider harness validation:
  `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py tests/scripts/test_production_dialogue_score.py tests/scripts/test_production_hook_score.py tests/scripts/test_production_cliffhanger_score.py tests/scripts/test_production_conflict_score.py tests/scripts/test_production_progression_score.py tests/scripts/test_provider_chain_api.py -q`
  passed: 26 passed, 27 warnings.
- File-size check:
  `wc -l ai-pic-backend/app/services/script/beat_contract_quality.py scripts/harness/production_dialogue_score.py ai-pic-backend/tests/unit/services/script/test_beat_contract_dialogue_quality.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py`
  showed changed Python files under repository hard limits: 216, 64, 33, and 46 lines.
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
- Pre-commit correction:
  intermediate staged-file runs failed because this new ledger was missing the required YAML frontmatter and then had an unquoted `date`; `scripts/check_agent_chats.py` and `docs/architecture/agent-workflow.md` identified the root cause, then the frontmatter was corrected and pre-commit was rerun.

## Next Steps

- Continue toward full commercial-grade proof with provider-backed generated samples and browser/provider-chain evidence; this slice proves a deterministic dialogue-length gate, not end-to-end generated script quality.
- Browser validation is not planned for this slice because it changes deterministic backend prompt/scoring helpers and harness tests, with no frontend, login, media-render, or API-surface change.

## Linked Commits

- Current commit: `feat(scripts): cap dialogue line length`.
