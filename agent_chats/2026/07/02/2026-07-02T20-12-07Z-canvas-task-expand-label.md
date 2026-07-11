---
id: 2026-07-02T20-12-07Z-canvas-task-expand-label
date: "2026-07-02T20:12:07Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - delivery
related_paths:
  - ai-pic-frontend/src/components/features/canvas
  - ai-pic-frontend/tests
summary: Records one increment of the production infinite canvas implementation and its validation.
---

## User Prompt

继续完善无限画布功能。

## Goals

- 修正大任务列表摘要的展开按钮文案，避免承诺会展开所有隐藏任务。
- 保留小任务列表的“展开全部任务（还有 N 条）”行为。
- 用单元测试和内置浏览器验证真实 `/canvas` 页面。

## Changes

- `ai-pic-frontend/src/components/features/canvas/ProductionCanvasTaskSummary.tsx`
  - 复用 `isTaskListCapped` 判断大任务列表。
  - 超过 20 个任务证据节点时，展开按钮显示 `展开最近 20 条`，aria 名称为 `展开最近 20 条任务`。
  - 小列表继续显示 `展开全部任务（还有 N 条）`。
- `ai-pic-frontend/tests/productionCanvasGraph.test.tsx`
  - 大列表测试断言旧的 `展开最近任务（还有 21 条）` 不再出现。
  - 大列表测试通过 `展开最近 20 条任务` 触发展开。

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> first run failed as expected before implementation because the old misleading label was still rendered; after implementation passed 11 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasBusyActions.test.tsx tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPlanner.test.tsx` -> passed 39 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> passed with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> passed 187 tests.

2. Browser validation:

- Entry URL: `http://localhost:8089/canvas?run_id=567b0cefc948467988f463e251e2b3b3`
- Environment: existing `dev_in_docker` stack, `ai-video-nginx` on `http://localhost:8089`.
- User path: opened the server-backed canvas run in the in-app browser, inspected the task summary, then clicked `展开最近 20 条任务`.
- Console: no warning or error entries.
- Network: no backend mutation was triggered; this was a DOM-only expand action after the run loaded.
- Result: task summary rendered `共 359`; old `展开最近任务（还有 ... 条）` text was absent; collapsed button rendered `展开最近 20 条`; clicking expanded the list to exactly 20 task rows and showed `收起任务列表`.
- Evidence artifact: `artifacts/runs/2026-07-02T20-12-07Z-canvas-task-expand-label/in-app-browser-result.json`

3. Conflict signals and corrections:

- Initial assumption: `展开最近任务（还有 N 条）` was acceptable because the action name said "recent".
- Contradicting evidence: in a 359-task run, the count text implied hundreds of hidden rows would be revealed even though the cap is 20.
- Reproduction and fix: updated the existing large-summary test to fail on the old text, then changed only the large-list label.
- Final verified state: tests and browser DOM both show capped lists use an explicit `20 条` label.

## Next Steps

- `npm run build`, `pre-commit run --all-files`, and `./docker/build_prod_images.sh` were not run because this was an uncommitted narrow component/test change; run them before publishing or committing.

## Linked Commits

- Not committed.
