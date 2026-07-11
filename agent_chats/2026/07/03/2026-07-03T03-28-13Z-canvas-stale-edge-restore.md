---
id: 2026-07-03T03-28-13Z-canvas-stale-edge-restore
date: "2026-07-03T03:28:13Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
summary: Filter stale production canvas edges during state restore.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - artifacts/runs/2026-07-03T03-28-13Z-canvas-stale-edge-restore/in-app-browser-result.json
---

## User Prompt

继续完善无限画布功能。用户补充：可以拉起 dev_in_docker，用内置浏览器检验。

## Goals

- 修复画布恢复时保留脏连线的问题。
- 覆盖恢复状态中存在缺失端点 edge 的回归测试。
- 用当前 dev_in_docker 运行环境和内置浏览器验证 `/canvas` 恢复路径。

## Changes

- 在 `createProductionCanvasState` 的 edge 克隆入口过滤端点不存在的连线。
- 在 `productionCanvasState.test.ts` 增加回归断言：只保留 `from`/`to` 都存在于当前节点集的 edge。
- 写入浏览器证据：`artifacts/runs/2026-07-03T03-28-13Z-canvas-stale-edge-restore/`。

## Validation

1. Local checks:

- Red check: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts` -> failed before the fix because `brief -> missing-node` was still present.
- Green check: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts` -> passed, 1/1.
- Canvas suite: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts')` -> passed, 75/75.
- Frontend lint: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> passed with 0 errors and 3 existing warnings.
- Frontend full tests: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> passed, 205/205.
- Repo docs: `python scripts/check_repo_docs.py` -> passed.
- Repo contracts: `python scripts/check_repo_contracts.py --mode audit` -> passed.

2. Browser or MCP validation:

- Environment: current `dev_in_docker` stack already running; `curl http://localhost:8089/canvas` returned HTTP 200.
- Entry URL: `http://localhost:8089/canvas?run_id=f69d1953ed7442f59bbb1a9c34ef5ce7`.
- Setup: local API created a temporary production canvas run, then saved state with nodes `brief` and `script`, valid edge `brief -> script`, and stale edge `brief -> missing-node`.
- Browser path: opened the run in the in-app browser, logged in with the repository test account when redirected, and let `/canvas?run_id=...` restore the run.
- Console: in-app browser dev logs had 0 errors and 0 warnings for the final validation.
- Result: page showed `已恢复`; visible canvas edge count was 1; edge editor showed `移除连线 Script`; `移除连线 missing-node` was absent.
- Evidence: `artifacts/runs/2026-07-03T03-28-13Z-canvas-stale-edge-restore/in-app-browser-result.json` and `artifacts/runs/2026-07-03T03-28-13Z-canvas-stale-edge-restore/canvas-stale-edge-restore.png`.

3. Conflict signals and corrections:

- Initial Chrome DevTools MCP attempt could not connect to `127.0.0.1:9222`; final browser validation used the in-app browser instead.
- The in-app browser read scope could not write `window.localStorage` directly, so the dirty restore state was prepared through the local authenticated API and then restored through the UI.

## Next Steps

- Keep continuing small, browser-verifiable infinite-canvas increments.
- Build was not run because this change only touches client-side canvas state logic and tests, not routes, layouts, auth, config, SSR, or hydration boundaries.

## Linked Commits

- Not committed.
