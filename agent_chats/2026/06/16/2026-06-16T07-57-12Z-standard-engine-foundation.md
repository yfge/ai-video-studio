---
id: 2026-06-16T07-57-12Z-standard-engine-foundation
date: "2026-06-16T07:57:12Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - standard-engine
  - repo-contracts
  - agent-workflow
related_paths:
  - scripts/standard_engine.py
  - scripts/contract_audit_reporting.py
  - tests/harness/test_repo_contracts.py
  - docs/standards/README.md
  - docs/architecture/contracts.md
summary: Add the first standard engine foundation by mapping repository contract checks to versioned standard IDs and docs.
---

## User Prompt

按这个思路进行standard engine 改造

## Goals

- Turn repository judgement rules into versioned standard objects.
- Attach standard IDs and repair directions to contract reports.
- Keep the first slice inside the existing docs, contract checker, and ledger
  workflow.

## Changes

- Added `scripts/standard_engine.py` with the standard catalog and category to
  standard mapping.
- Updated `scripts/contract_audit_reporting.py` so mechanical contract
  violations and docs drift include standard metadata.
- Added `docs/standards/` with active standards for architecture, data access,
  docs drift, validation evidence, and production script quality.
- Updated `docs/README.md` and `docs/architecture/contracts.md` to document the
  standard engine contract surface.
- Added harness tests for standard metadata in contract reports.

## Validation

- `python -m pytest tests/harness/test_repo_contracts.py -q`: passed
  (`5 passed`).
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff ...`: passed for the
  standard engine files, docs, tests, and ledger.
- `python scripts/check_repo_contracts.py --mode audit --report-json
/tmp/standard-engine-contracts.json --report-md
/tmp/standard-engine-contracts.md`: passed without failing audit mode.
- `python -c 'from scripts.check_agent_chats import validate_agent_file; ...'`:
  passed for this ledger entry.
- `git diff --check`: passed.

## Next Steps

- Extend product quality harnesses to emit standard IDs in a later slice.

## Linked Commits

- Pending commit.
