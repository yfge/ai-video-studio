---
id: 2026-07-03T08-41-17Z-canvas-active-run-execute
date: "2026-07-03T08:41:17Z"
participants: [human, codex]
models: [gpt-5-codex]
tags: [canvas, frontend, browser-validation]
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/tests/productionCanvasSkillPlannerRunId.test.tsx
summary: "Bind canvas skill execution to the active Run ID and verify the restored canvas path in the in-app browser."
---

## User Prompt

现在整体链路还是断的

## Goals

- Reproduce the broken `/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6` execution path in the real in-app browser.
- Keep manual node execution bound to the active canvas Run ID instead of stale node output.
- Preserve existing node-output fallback behavior for runs that do not yet have an active Run ID.

## Changes

- Added `currentRunId` to `useProductionCanvasSkillPlanner`.
- Passed `persistence.runId` from `ProductionCanvasBoard` into the planner.
- Changed skill execution requests to prefer the active canvas Run ID, falling back to `node.outputs.canvas_run_id`.
- Added a focused hook-level regression test for stale node `canvas_run_id` execution.

## Validation

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasSkillPlannerRunId.test.tsx` failed before the fix with actual `stale-run` vs expected `current-run`.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasSkillPlannerRunId.test.tsx` passed after the fix.
- `cd ai-pic-frontend && npm run lint` passed with the existing 3 warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run test` was attempted; the full run printed passing results through the canvas/planner/run-id suites and then hung in an unrelated current-worktree `tests/toastProvider.test.tsx` child process, so it was interrupted with Ctrl-C.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasSkillPlannerRunId.test.tsx tests/productionCanvasPlanner.test.tsx tests/productionCanvasRunPersistence.test.ts tests/productionCanvasPersistence.test.tsx` passed: 23 tests.
- `cd ai-pic-frontend && npm run build` passed.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/tests/productionCanvasSkillPlannerRunId.test.tsx agent_chats/2026/07/03/2026-07-03T08-41-17Z-canvas-active-run-execute.md` passed after keeping `ProductionCanvasBoard.tsx` under the 250-line file-size limit.
- `pre-commit run --files ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/tests/productionCanvasSkillPlannerRunId.test.tsx agent_chats/2026/07/03/2026-07-03T08-41-17Z-canvas-active-run-execute.md` passed.
- In-app browser entry URL: `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Browser evidence before fix: visible Run ID was `48d62cd56e1646c4b3f0c77c1a3cd4a6`, but backend logs showed `POST /api/v1/production-canvas/execute` body used `run_id: 0cae5687386f4697ae52d9eb6c3e6580`.
- Browser evidence after fix: the same selected Asset Selection execute action sent `run_id: 48d62cd56e1646c4b3f0c77c1a3cd4a6`; the follow-up autosave wrote to `/api/v1/production-canvas/runs/48d62cd56e1646c4b3f0c77c1a3cd4a6/state` with HTTP 200.
- Console evidence after reload and execute had no material new errors; only React DevTools and HMR informational messages were observed.
- Evidence artifact: `artifacts/runs/canvas-run-id-execute-20260703T084117Z/evidence.json`.

## Next Steps

- Continue reducing remaining chain blockers from the current `48d62cd56e1646c4b3f0c77c1a3cd4a6` run after this run-id split is committed.

## Linked Commits

- Pending.
