---
id: 2026-07-03T07-49-04Z-canvas-graph-state-updates
date: "2026-07-03T07:49:04Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - state
summary: Added reusable canvas graph node update helpers.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasGraphState.ts
  - ai-pic-frontend/tests/productionCanvasGraphState.test.ts
---

## User Prompt

- `/goal 继续完善无限画布功能,保持原子化提交`

## Goals

- Centralize canvas node removal so connected edges are removed in one place.
- Centralize node patching so output fields can be merged and cleared consistently.

## Changes

- Added `removeProductionCanvasNode`.
- Added `updateProductionCanvasNode`.
- Added focused graph-state tests for edge cleanup and output-key removal.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasGraphState.test.ts` -> pass, 2 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/productionCanvasGraphState.ts ai-pic-frontend/tests/productionCanvasGraphState.test.ts` -> pass.

Browser validation:

- Not run for this slice because it changes pure graph state helpers.

## Next Steps

- Wire these helpers through the remaining canvas note and task UI slices.

## Linked Commits

- This commit.
