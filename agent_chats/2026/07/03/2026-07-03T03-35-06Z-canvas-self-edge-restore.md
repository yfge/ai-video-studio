---
id: 2026-07-03T03-35-06Z-canvas-self-edge-restore
date: "2026-07-03T03:35:06Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
summary: Filter self-loop production canvas edges during state restore.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - artifacts/runs/2026-07-03T03-35-06Z-canvas-self-edge-restore/in-app-browser-result.json
---

## User Prompt

继续完善无限画布功能。用户补充：可以拉起 dev_in_docker，用内置浏览器检验。

## Goals

- 修复画布恢复时保留自环连线的问题。
- 用回归测试覆盖保存状态中存在 `brief -> brief` self-loop edge 的场景。
- 用当前 dev_in_docker 运行环境和内置浏览器验证 `/canvas` 恢复路径。

## Changes

- 在 `createProductionCanvasState` 的 edge 克隆入口过滤 `from === to` 的自环连线。
- 在 `productionCanvasState.test.ts` 增加回归断言：保存状态同时包含有效边、缺失端点边和自环边时，只保留有效边。
- 写入浏览器证据：`artifacts/runs/2026-07-03T03-35-06Z-canvas-self-edge-restore/`。

## Validation

1. Local checks:

- Red check: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts` -> failed before the fix because `brief -> brief` was still present.
- Green check: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts` -> passed, 1/1.
- Canvas suite: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts')` -> passed, 75/75.
- Frontend lint: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> passed with 0 errors and 3 existing warnings.
- Frontend full tests: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> passed, 205/205.
- Repo docs: `python scripts/check_repo_docs.py` -> passed.
- Repo contracts: `python scripts/check_repo_contracts.py --mode audit` -> passed.

2. Browser or MCP validation:

- Environment: current `dev_in_docker` stack was already running; validation used `http://localhost:8089`.
- Entry URL: `http://localhost:8089/canvas?run_id=9d468119784547a1a51f71ccc30ca70b`.
- Setup: local API created a temporary production canvas run, then saved state with nodes `brief` and `script`, valid edge `brief -> script`, and self-loop edge `brief -> brief`.
- Browser path: opened the run in the in-app browser and let `/canvas?run_id=...` restore the run.
- Console: in-app browser dev logs had 0 errors and 0 warnings for the final validation.
- Result: page showed `已恢复`; visible canvas edge count was 1; edge editor showed `移除连线 Script`; `移除连线 Brief` was absent.
- Evidence: `artifacts/runs/2026-07-03T03-35-06Z-canvas-self-edge-restore/in-app-browser-result.json` and `artifacts/runs/2026-07-03T03-35-06Z-canvas-self-edge-restore/canvas-self-edge-restore.png`.

3. Conflict signals and corrections:

- Chrome DevTools MCP could not connect to `127.0.0.1:9222`; final browser validation used the in-app browser fallback and recorded that explicitly.

## Next Steps

- Keep continuing small, browser-verifiable infinite-canvas increments.
- Build was not run because this change only touches client-side canvas state logic and tests, not routes, layouts, auth, config, SSR, or hydration boundaries.

## Linked Commits

- Not committed.
