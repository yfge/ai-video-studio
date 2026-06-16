---
id: 2026-06-16T08-02-51Z-script-standard-output
date: "2026-06-16T08:02:51Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - standard-engine
  - script-quality
  - harness
related_paths:
  - scripts/standard_engine.py
  - scripts/harness/production_quality_script.py
  - scripts/harness/production_structured_score.py
  - scripts/harness/production_script_quality_aggregate.py
  - ai-pic-backend/tests/scripts/test_production_quality_regression.py
  - ai-pic-backend/tests/scripts/test_production_script_quality_regression.py
  - docs/standards/STD-SCRIPT-001.md
summary: Attach STD-SCRIPT-001 metadata to production script quality scores and aggregate reports.
---

## User Prompt

按这个思路进行standard engine 改造

## Goals

- Move the standard engine beyond repository structure checks.
- Make production script quality evidence explicitly cite `STD-SCRIPT-001`.
- Preserve existing script scoring and aggregate behavior while adding audit
  metadata.

## Changes

- Added a reusable `standard_reference()` helper to `scripts/standard_engine.py`.
- Added `STD-SCRIPT-001` metadata to `structured_script_score()` outputs.
- Added `STD-SCRIPT-001` metadata to script quality aggregate reports.
- Restored the `production_quality_script` facade export for
  `STRUCTURED_SCORE_PASS` and `structured_script_score`, which is the import
  path used by existing production quality modules and tests.
- Extended focused script quality tests to assert standard metadata.

## Validation

- `python -m pytest ai-pic-backend/tests/scripts/test_production_script_quality_regression.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`:
  first run failed during collection because `production_quality_script` did
  not export `STRUCTURED_SCORE_PASS`; rerun passed with `22 passed`.
- `python -m pytest ai-pic-backend/tests/scripts/test_production_hook_score.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py -q`:
  passed with `17 passed`.
- `python -m pytest tests/harness/test_repo_contracts.py -q`: passed with
  `5 passed`.
- `python scripts/check_repo_docs.py`: passed.
- `{ git diff --name-only; git ls-files --others --exclude-standard; } | sort
-u | xargs python scripts/check_repo_contracts.py --mode diff`: passed.
- `python scripts/check_repo_contracts.py --mode audit --report-json
/tmp/standard-engine-contracts.json --report-md
/tmp/standard-engine-contracts.md`: passed.
- Ledger file validation for both standard engine entries: passed.
- `git diff --check`: passed.
- Direct smoke of `structured_script_score()` and
  `aggregate_script_quality_report()` confirmed both output
  `STD-SCRIPT-001 docs/standards/STD-SCRIPT-001.md`.

## Next Steps

- Extend Timeline/browser harness evidence to standard IDs in a later slice.

## Linked Commits

- Pending commit.
