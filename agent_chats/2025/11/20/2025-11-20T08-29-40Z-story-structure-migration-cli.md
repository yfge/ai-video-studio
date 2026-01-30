---
id: 2025-11-20T08-29-40Z-story-structure-migration-cli
date: 2025-11-20T08:29:40Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, migration]
related_paths:
  - ai-pic-backend/scripts/prototype_story_structure_migration.py
  - docs/story-structure-gap-analysis.md
  - task.md
summary: "Added reporting/dry-run improvements to migration prototype script and updated migration checklist/next actions."
---

## User Prompt

- "check task and continue"

## Goals

- Extend the migration prototype script to support dry-run reporting and clearer fallbacks for normalized story structure backfill.
- Update documentation and task board to reflect the new CLI flow and next validation steps.

## Changes

- Added extraction warnings, defaults, original_json audit metadata, and JSON report output (`--report-path`) to `prototype_story_structure_migration.py`; probe insert now returns structured results and tracks skips.
- Documented CLI usage for dry run and insert probe in `docs/story-structure-gap-analysis.md` migration plan section.
- Adjusted `task.md` migration next action to run the live insert-probe with report and add pytest coverage.

## Validation

- `cd ai-pic-backend && pytest` (timed out around 20% with existing failing cases; no new failures triaged in this pass).

## Next Steps

- Execute live `--insert-probe` against sample script IDs and review the generated report for skips/warnings.
- Add pytest coverage for dry-run and probe flows, including fallback slug/time defaults.

## Linked Commits

- (this commit)
