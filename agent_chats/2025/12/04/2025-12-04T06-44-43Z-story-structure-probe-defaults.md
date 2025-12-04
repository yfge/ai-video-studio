---
id: 2025-12-04T06-44-43Z-story-structure-probe-defaults
date: 2025-12-04T06:44:43Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/scripts/prototype_story_structure_migration.py
  - ai-pic-backend/tests/scripts/test_prototype_story_structure_migration.py
summary: "Hardened story structure insert probe defaults and validated live run via SQLite fixture"
---
## User Prompt
推进迁移脚本验证

## Goals
- Run `prototype_story_structure_migration.py` in live mode with `--insert-probe` and capture a report.
- Ensure the probe handles schemas lacking server defaults (SQLite/dev paths) without failing.

## Changes
- Added fallback `is_deleted` + timestamp defaults in the insert probe to survive DBs without server defaults.
- Parameterized the test schema helper to toggle server defaults and covered the missing-default case.
- Executed a live probe against a SQLite-backed sample script (id 3001) to confirm counts and rollback behaviour.

## Validation
- `cd ai-pic-backend && pytest tests/scripts/test_prototype_story_structure_migration.py`
- `DATABASE_URL=sqlite:////tmp/story_structure_probe.db python scripts/prototype_story_structure_migration.py --mode live --script-id 3001 --dsn sqlite:////tmp/story_structure_probe.db --insert-probe --report-path /tmp/story_structure_probe_report.json` (counts: treatments=1, outlines=3, scenes=3, beats=6, shots=3; warnings: none; rolled_back: true)

## Next Steps
- Re-run the probe against the real MySQL instance once available (with an actual script id) and archive the report.
- Align Base models/alembic defaults to avoid SQLite drift, or document the SQLite seeding recipe for probes.

## Linked Commits
- (pending)
