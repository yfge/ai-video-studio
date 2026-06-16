---
id: 2026-06-16T08-06-25Z-timeline-standard-output
date: "2026-06-16T08:06:25Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - standard-engine
  - timeline
  - harness
related_paths:
  - scripts/standard_engine.py
  - scripts/harness/production_quality_aggregate.py
  - scripts/harness/production_quality_gates.py
  - scripts/harness/production_quality_regression.py
  - ai-pic-backend/tests/scripts/test_production_quality_regression.py
  - ai-pic-backend/tests/scripts/test_production_standard_metadata.py
  - docs/standards/STD-TIMELINE-001.md
summary: Attach STD-TIMELINE-001 metadata to Timeline-first provider-chain quality evidence.
---

## User Prompt

按这个思路进行standard engine 改造

## Goals

- Extend the standard engine into Timeline-first runtime evidence.
- Make provider-chain quality reports cite the standard they prove.
- Keep existing gate semantics unchanged while adding audit metadata.

## Changes

- Added `STD-TIMELINE-001` to the standard catalog and docs.
- Added Timeline standard metadata to provider-chain sample reports, Timeline
  order gates, render gates, character consistency gates, and aggregate quality
  reports.
- Added `standard_ids` to production quality run summaries.
- Added focused production standard metadata tests without growing the existing
  production quality regression file beyond the file-size contract.

## Validation

- `python -m pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q`:
  passed with `16 passed`.
- After `STD-ARCH-001` flagged
  `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  at `line_count=303`, the standard metadata assertions were moved into
  `test_production_standard_metadata.py`; rerun with both files passed with
  `20 passed`.
- `python -m pytest tests/harness/test_common.py tests/harness/test_repo_contracts.py -q`:
  passed with `8 passed`.
- Changed-files `python scripts/check_repo_contracts.py --mode diff`: passed
  after the test split.
- Ledger file validation for all three standard engine entries: passed.

## Next Steps

- Extend browser-flow summaries to `STD-EVIDENCE-001` in a later slice.

## Linked Commits

- Pending commit.
