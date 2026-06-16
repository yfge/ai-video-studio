---
id: 2026-06-16T08-09-31Z-runtime-evidence-standard
date: "2026-06-16T08:09:31Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - standard-engine
  - browser-evidence
  - harness
related_paths:
  - scripts/harness/_common.py
  - scripts/harness/browser_flow.py
  - scripts/harness/run_golden_path.py
  - tests/harness/test_common.py
  - tests/harness/test_runtime_evidence_standards.py
  - docs/standards/STD-EVIDENCE-001.md
summary: Attach STD-EVIDENCE-001 metadata to browser and golden-path runtime evidence artifacts.
---

## User Prompt

按这个思路进行standard engine 改造

## Goals

- Connect browser and golden-path runtime artifacts to the standard engine.
- Make durable validation evidence cite `STD-EVIDENCE-001`.
- Avoid requiring a live browser or backend for the new unit coverage.

## Changes

- Added `_common.standard_fields()` for reusable standard references in harness
  artifacts.
- Added `STD-EVIDENCE-001` metadata to `browser_flow.json`,
  `golden_path.json`, and their `summary.json` updates.
- Updated `STD-EVIDENCE-001` docs to require standard metadata in durable
  runtime artifacts.
- Added focused tests for browser-flow and golden-path standard metadata.

## Validation

- `python -m pytest tests/harness/test_runtime_evidence_standards.py tests/harness/test_common.py -q`:
  passed with `6 passed`.
- `python -m pytest tests/harness/test_common.py tests/harness/test_repo_contracts.py tests/harness/test_runtime_evidence_standards.py -q`:
  passed with `11 passed`.
- `python -m pytest ai-pic-backend/tests/scripts/test_production_script_quality_regression.py ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_standard_metadata.py -q`:
  passed with `26 passed`.
- `python scripts/check_repo_docs.py`: passed.
- Changed-files `python scripts/check_repo_contracts.py --mode diff`: passed.
- `python scripts/check_repo_contracts.py --mode audit --report-json
/tmp/standard-engine-contracts.json --report-md
/tmp/standard-engine-contracts.md`: passed.
- `git diff --check`: passed.

## Next Steps

- Review whether the current standard engine coverage is sufficient to close
  the goal or whether another runtime surface needs standard metadata.

## Linked Commits

- Pending commit.
