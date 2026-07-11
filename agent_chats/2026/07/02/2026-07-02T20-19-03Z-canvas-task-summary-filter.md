---
id: 2026-07-02T20-19-03Z-canvas-task-summary-filter
date: "2026-07-02T20:19:03Z"
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

- 让任务证据摘要里的状态胶囊可以筛选列表，方便在大画布里快速看异常、生成中或已完成任务。
- 保留状态胶囊定位最新匹配任务的能力。
- 避免筛选后绕开大列表的最近 20 条刷新保护。

## Changes

- `ai-pic-frontend/src/components/features/canvas/ProductionCanvasTaskSummary.tsx`
  - 增加本地 `taskFilter` 状态。
  - 新增 `全部` 胶囊，状态胶囊支持按 `生成中`、`已完成`、`异常` 过滤可见任务行。
  - 有 `onSelectNode` 时，状态胶囊继续定位最新匹配任务，并在 aria 名称中标明 `定位并筛选...任务`。
  - 大列表刷新保护改为基于总任务数判断，筛选到少量任务后仍保持 `刷新最近任务`。
  - 展开按钮基于过滤后的可见列表判断，避免出现 `还有 0 条`。
- `ai-pic-frontend/tests/productionCanvasGraph.test.tsx`
  - 增加状态胶囊筛选测试。
  - 增加筛选后仍保持最近 20 条刷新保护的回归测试。
- `ai-pic-frontend/tests/productionCanvasPlanner.test.tsx`
  - 更新状态胶囊 aria 名称，并在定位后切回 `全部` 以继续后续失败任务断言。

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> first run failed as expected because no status filter buttons existed; after implementation passed 13 tests.
- After browser found the filtered-refresh regression, `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` failed as expected because the filtered summary exposed `刷新全部任务`; after separating display and refresh caps, passed 13 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasBusyActions.test.tsx tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPlanner.test.tsx` -> passed 41 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> passed with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> passed 189 tests.

2. Browser validation:

- Entry URL: `http://localhost:8089/canvas?run_id=567b0cefc948467988f463e251e2b3b3`
- Environment: existing `dev_in_docker` stack, `ai-video-nginx` on `http://localhost:8089`.
- User path: opened the server-backed canvas run in the in-app browser, clicked `定位并筛选异常任务`, then clicked `筛选全部任务`.
- Console: no warning or error entries.
- Network: no backend mutation was triggered; this was a DOM-only filter interaction after the run loaded.
- Result: summary rendered `共 359`; failed filter reduced visible rows to 1, marked `异常 1` pressed, kept `刷新最近任务`, and did not show `还有 0 条`; switching back to `全部 359` restored the default 4 recent rows.
- Evidence artifact: `artifacts/runs/2026-07-02T20-19-03Z-canvas-task-summary-filter/in-app-browser-result.json`

3. Conflict signals and corrections:

- Initial implementation reused the filtered list cap for refresh behavior.
- Browser evidence showed that filtering to 1 failed task changed the refresh button back to `刷新全部任务`, which could refresh all 359 tasks.
- Added a regression test for filtered large summaries and split display cap from refresh cap.

## Next Steps

- `npm run build`, `pre-commit run --all-files`, and `./docker/build_prod_images.sh` were not run because this was an uncommitted narrow component/test change; run them before publishing or committing.

## Linked Commits

- Not committed.
