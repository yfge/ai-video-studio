---
id: 2026-07-03T08-11-19Z-canvas-initial-run-restore
date: "2026-07-03T08:11:19Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - persistence
summary: Added initial run id restore support to the canvas persistence hook.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts
  - ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts
---

# Canvas Initial Run Restore

## User Prompt

- `/goal 继续完善无限画布功能,保持原子化提交`

## Goals

- Let the canvas persistence hook restore a run when it receives an initial Run ID.
- Prevent autosave from overwriting a linked run before the initial restore has loaded.

## Changes

- Added an optional `initialRunId` input to `useProductionCanvasRunPersistence`.
- Reused `productionCanvasRunIdFromInput` so initial values can be raw IDs or pasted canvas links.
- Deferred autosave while an initial run is pending restore and no restored signature exists yet.
- Added a focused hook test that delays the restore response and proves autosave does not fire first.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasRunPersistence.test.ts` -> pass, 2 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts agent_chats/2026/07/03/2026-07-03T08-11-19Z-canvas-initial-run-restore.md` -> pass.
- `cd ai-pic-frontend && npm run lint` -> pass, 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` -> pass.
- `pre-commit run --files ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts agent_chats/2026/07/03/2026-07-03T08-11-19Z-canvas-initial-run-restore.md` -> pass.

2. Browser or MCP validation:

- Not run for this hook-only slice; route wiring and browser validation remain for a later canvas URL restore slice.

3. Conflict signals and corrections:

- Initial assumption: URL synchronization could be committed with initial restore.
- Contradicting evidence: URL synchronization without page-level query wiring could clear an existing `run_id` before the page consumes it.
- Reproduction and fix: narrowed this commit to hook-level initial restore and autosave protection only.
- Final verified state: targeted hook tests, repo contracts, docs check, lint, and scoped pre-commit passed.

## Next Steps

- Wire `/canvas?run_id=...` through the page and board in a separate route-aware commit.
- Add URL synchronization and reset clearing after route wiring is staged.

## Linked Commits

- Pending.
