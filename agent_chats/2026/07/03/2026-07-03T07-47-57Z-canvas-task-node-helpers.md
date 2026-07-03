---
id: 2026-07-03T07-47-57Z-canvas-task-node-helpers
date: "2026-07-03T07:47:57Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - task-evidence
summary: Shared task evidence labels and task node links.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasSkillNodes.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasTaskSummaryModel.ts
  - ai-pic-frontend/tests/productionCanvasSkillNodes.test.ts
---

## User Prompt

- `/goal 继续完善无限画布功能,保持原子化提交`

## Goals

- Give task evidence nodes reusable status metadata for canvas cards and inspectors.
- Keep task status labels sourced from one shared mapping.
- Deep-link generated task evidence nodes to their task detail route.

## Changes

- Exported `taskStatusLabelForStatus` from the task summary model.
- Reused that mapper from `productionCanvasSkillNodes`.
- Added task-aware node status metadata and a manual-note guard.
- Changed generated task evidence links from `/tasks` to `/tasks?task_id=<id>`.
- Added focused tests for task status metadata, manual-note detection, and task deep links.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasSkillNodes.test.ts` -> pass, 3 tests.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/productionCanvasSkillNodes.ts ai-pic-frontend/src/components/features/canvas/productionCanvasTaskSummaryModel.ts ai-pic-frontend/tests/productionCanvasSkillNodes.test.ts` -> pass.
- `cd ai-pic-frontend && npm run lint` -> pass with 0 errors and 3 existing warnings.
- `python scripts/check_repo_docs.py` -> pass.

Browser validation:

- Not run for this slice because it changes pure mapping/link helper behavior.

## Next Steps

- Continue splitting the remaining canvas UI integration changes into focused commits.

## Linked Commits

- This commit.
