---
id: 2026-07-02T19-19-34Z-canvas-task-refresh-error-node
date: "2026-07-02T19:19:34Z"
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

继续完善无限画布功能。用户补充可以拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- 让任务刷新失败不只停留在右侧 alert，也写回对应任务证据节点。
- 保持单任务刷新错误仍然只显示在失败节点范围内。
- 避免为旧任务证据增加新的状态系统或额外存储结构。

## Changes

- `useProductionCanvasTaskSync.ts` 增加 `taskRefreshErrorPatch`，刷新任务失败时把对应节点标为 `blocked`，并写入 `任务 #... 刷新失败：...` 详情。
- 单个任务刷新和批量 `刷新全部` 的失败 catch 复用同一 patch。
- `productionCanvasPlanner.test.tsx` 在既有任务刷新错误用例中新增红绿断言：失败节点出现刷新失败详情，并且节点卡片显示 `待补齐`。

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx` -> red before implementation: failed because `任务 #101 刷新失败：任务刷新失败` was not rendered.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx` -> pass after implementation, 8 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx tests/productionCanvasPlanner.test.tsx` -> pass, 14 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasBusyActions.test.tsx tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPlanner.test.tsx` -> pass, 33 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> pass with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> pass, 181 tests.
- `npm run build` omitted because this is a client hook behavior change with no route, layout, config, auth redirect, SSR boundary, or hydration-sensitive change.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas` through the existing dev_in_docker stack.
- User path: opened `/canvas`, logged in as the repository test user, confirmed the canvas shell rendered as `geyunfei`, selected an existing task evidence node, and confirmed the task refresh action remained available.
- Console: no browser error or warning entries.
- Result: current task evidence detail displayed `任务 #44 当前状态 失败；进度：'dict_items' object has no attribute 'items'；错误：'dict_items' object has no attribute 'items'`. Evidence saved to `artifacts/runs/2026-07-02T19-19-34Z-canvas-task-refresh-error-node/in-app-browser-result.json`.

3. Conflict signals and corrections:

- Initial assumption: an old visible `Task #1` node could be used to prove the missing-task refresh path in-browser.
- Contradicting evidence: the persisted canvas has many overlapping old nodes; clicking the visible `Task #1` landed on the currently selected task #44 area.
- Reproduction and fix: kept the precise stale-refresh writeback proof in the red-green component test and used the browser for route/auth/refresh-surface smoke without mutating browser local storage.
- Final verified state: local tests prove failed refreshes mark the specific task node as blocked with a visible detail; browser smoke proves `/canvas` still loads and task refresh UI remains usable in dev_in_docker.

## Next Steps

- Continue reducing friction from very large persisted canvas task lists.
- If stale local task ids are common in production data, add a small explicit stale-task label in the task summary.

## Linked Commits

- None in this working tree slice.
