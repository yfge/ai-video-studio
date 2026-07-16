---
id: 2026-07-16T10-23-33Z-canvas-focused-layout
date: "2026-07-16T10:23:33Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - frontend
  - product-design
  - browser-validation
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasExecutionView.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasChatBar.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasWorkspace.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasSidePanel.tsx
  - design-qa.md
summary: Recompose the infinite Production Canvas around one creation surface, one graph workspace, and one contextual inspector.
---

## User Prompt

现在无限画布功能的页面是不是太乱了。先出一版设计图。按这个进行优化。

## Goals

- Implement the selected focused Production Canvas mock without changing the
  underlying planning, execution, persistence, or candidate-review behavior.
- Keep the creation goal as the first action and give the graph the largest stable
  area.
- Collapse secondary run, filter, context, collaboration, and diagnostic controls.
- Use one contextual right inspector and remove redundant explanatory cards.
- Prove the result against the reference image in a real browser.

## Changes

- Moved the prompt-first creation form into a full-width card above the canvas.
- Added a compact context summary with expandable production parameters and moved
  run management into a collapsed `运行详情` disclosure.
- Replaced the permanent filter and viewport toolbars with floating canvas controls;
  kept undo, redo, zoom, fit, focus, filters, templates, notes, save, restore, and
  run actions intact.
- Reduced the canvas row to the graph plus one selected-node inspector. The
  inspector disappears with no selection and collaboration is lazy/collapsed.
- Removed the `引用对象`, `执行层`, and `证据出口` footer cards, added a slim live
  status footer, and made node ports appear on hover/focus instead of permanently.
- Added default-collapsed and dynamic-inspector regression assertions.
- Added `design-qa.md` and browser artifacts for the reference comparison.

## Validation

- Changed-file ESLint -> passed with no output.
- `npm run lint` -> passed with 0 errors and 3 pre-existing warnings.
- Focused Canvas regression after final changes:
  `productionCanvasBoard`, `productionCanvasToolbarFocus`,
  `productionCanvasPersistence`, and `productionCanvasPlanner` -> 33/33 passed.
- Full frontend suite -> 419/422 passed. The three failures were isolated to test
  process concurrency and duplicate status copy; after the copy fix,
  `productionCanvasPersistence` passed 9/9 and `productionCanvasPlanner` passed
  10/10 independently.
- `npm run build` -> passed, including TypeScript and all 16 static pages.
- Chrome DevTools transport was attempted twice and returned HTTP 404 at
  `127.0.0.1:9222`; the recorded Playwright fallback opened authenticated
  `http://localhost:8090/canvas` successfully.
- Playwright interaction evidence verified collapsed/open/closed states for
  production parameters, run details, and filters; inspector close/reopen; removal
  of the old footer cards; and zero console errors, page errors, or failed responses.
- Side-by-side visual QA is recorded in `design-qa.md` with
  `final result: passed`.
- `python scripts/check_repo_docs.py` and the changed-file repository contract
  check -> passed.
- `pre-commit run --all-files` was attempted but hit the repository-wide baseline:
  69 remaining Ruff errors and the existing backend quick-gate import failure for
  `coerce_timeline_shot_plan_payload`. Its unrelated autoformat edits were reverted.
- Scoped `pre-commit run --files <18 Canvas paths>` -> passed, including Prettier,
  repository docs/contracts, ledger enforcement, and frontend lint; backend hooks
  were correctly skipped because this slice contains no backend files.
- Final focused Canvas regression after hook formatting -> 33/33 passed.
- The default multi-platform `./docker/build_prod_images.sh` could not pass Docker
  Hub metadata resolution through the configured container-driver builder and was
  cancelled without changing the worktree. The legacy no-push fallback also hung
  while transporting the repository context.
- Equivalent no-push ARM64 production builds from the exact staged 24 MB Git
  context passed with Docker Desktop's BuildKit driver: the backend image installed
  system and Python dependencies successfully, and the frontend image completed
  `npm ci`, TypeScript, all 16 Next.js pages, and the runtime dependency layer.

## Next Steps

- Optional: investigate the repository-wide frontend test runner's shared global
  `fetch` interference so the full parallel run is deterministically green.
- Chrome DevTools evidence can replace the recorded Playwright fallback after the
  stale local debugging endpoint on port 9222 is repaired.

## Linked Commits

- This ledger is committed with the implementation.
