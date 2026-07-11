---
id: "2026-07-03T03-48-14Z-canvas-duplicate-node-restore"
date: "2026-07-03T03:48:14Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
  - browser-validation
summary: "Dedupe restored production canvas nodes."
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - artifacts/runs/2026-07-03T03-47-15Z-canvas-duplicate-node-restore/in-app-browser-result.json
---

## User Prompt

/goal 继续完善无限画布功能

用户补充：可以拉起 dev_in_docker，用内置浏览器检验。

## Goals

- Keep restored canvas state stable when persisted state contains duplicate node IDs.
- Validate through unit coverage and a real Docker-backed browser restore path.

## Changes

- Added restore-time node ID de-duplication in `createProductionCanvasState`, preserving the first node for each ID.
- Reused the de-duplicated nodes for edge filtering, context application, and selected-node fallback.
- Added state test coverage for a duplicated `brief` node.

## Validation

- Red check before implementation:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Failed because restored nodes included two `brief` entries.
- Green focused state check:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Passed: 2 tests.
- File size:
  - `wc -l ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts ai-pic-frontend/tests/productionCanvasState.test.ts`
  - State file remained 249 lines.
- Canvas subset:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts')`
  - Passed: 76 tests.
- Frontend lint:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint`
  - Passed with 3 existing warnings.
- Docker stack:
  - `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | rg 'ai-video|NAMES'`
  - `ai-video-nginx`, `ai-video-frontend`, `ai-video-backend`, `ai-video-mysql`, `ai-video-redis`, `ai-video-celery-worker`, and `ai-video-celery-beat` were running.
- Real browser validation:
  - Used the in-app browser requested by the user.
  - Created run `8f7253403e3c437a84716034b385700a` through `http://localhost:8000/api/v1/production-canvas/plan`.
  - Saved three persisted nodes through `PUT /api/v1/production-canvas/runs/8f7253403e3c437a84716034b385700a/state`, including two `brief` nodes.
  - Opened `http://localhost:8089/canvas?run_id=8f7253403e3c437a84716034b385700a`.
  - Result: page showed `已恢复`, `[data-canvas-node='brief']` count was 1, the duplicate title `Duplicate brief` was not visible, `script` count was 1, rendered edge was `brief-script`, and browser warn/error logs were empty.
  - Evidence: `artifacts/runs/2026-07-03T03-47-15Z-canvas-duplicate-node-restore/in-app-browser-result.json`, `artifacts/runs/2026-07-03T03-47-15Z-canvas-duplicate-node-restore/canvas-duplicate-node-restore.png`.
- Full frontend tests:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test`
  - Passed: 206 tests.
- Repo docs:
  - `python scripts/check_repo_docs.py`
  - Passed.
- Repo contracts:
  - `python scripts/check_repo_contracts.py --mode audit`
  - Passed.
- `npm run build` skipped because this was a client state-normalization change only, with no route, layout, auth, config, SSR, or hydration-sensitive change.

## Next Steps

- Continue the active infinite canvas goal with another narrow canvas behavior increment.

## Linked Commits

- Pending commit.
