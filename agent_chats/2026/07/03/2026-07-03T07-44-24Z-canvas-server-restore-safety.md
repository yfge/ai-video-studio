---
id: 2026-07-03T07-44-24Z-canvas-server-restore-safety
date: "2026-07-03T07:44:24Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - persistence
summary: Sanitized server-restored infinite canvas state.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPersistence.ts
  - ai-pic-frontend/tests/productionCanvasServerRestore.test.ts
---

## User Prompt

- `/goal 继续完善无限画布功能,保持原子化提交`

## Goals

- Keep server-restored canvas runs stable when saved state contains bad geometry or stale edges.
- Reuse existing canvas geometry cleanup instead of duplicating restore logic.

## Changes

- Reused `finiteCanvasNumber` and `clampProductionCanvasZoom` in server restore conversion.
- Kept server plan nodes, saved server nodes, and viewport values inside the same safe ranges as local restores.
- Added focused pure-function tests for invalid plan node geometry, duplicate nodes, duplicate/self/stale edges, invalid dimensions, invalid viewport values, and stale selected node ids.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasServerRestore.test.ts` -> pass, 2 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/productionCanvasPersistence.ts ai-pic-frontend/tests/productionCanvasServerRestore.test.ts` -> pass.

Browser validation:

- Not run for this slice because it changes pure saved-state conversion logic without a browser-only path.

## Next Steps

- Continue splitting the remaining infinite canvas UI work into atomic commits.

## Linked Commits

- This commit.
