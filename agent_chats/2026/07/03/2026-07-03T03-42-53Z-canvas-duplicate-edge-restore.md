---
id: "2026-07-03T03-42-53Z-canvas-duplicate-edge-restore"
date: "2026-07-03T03:42:53Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
  - browser-validation
summary: "Dedupe restored production canvas edges."
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - artifacts/runs/2026-07-03T03-41-42Z-canvas-duplicate-edge-restore/in-app-browser-result.json
---

## User Prompt

/goal 继续完善无限画布功能

你可以拉起 dev_in_docker 用内置浏览器检验

## Goals

- Keep restored canvas edges usable when persisted state contains duplicate edge rows.
- Validate the fix through the running Docker stack and the in-app browser.

## Changes

- Added restore-time edge de-duplication in `createProductionCanvasState` while preserving the existing guards for self-loop and missing-endpoint edges.
- Added state test coverage that saves a duplicated `brief -> script` edge and expects only one restored edge.

## Validation

- Red check before implementation:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Failed because duplicate `brief -> script` edges were preserved.
- Green focused state check:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Passed: 1 test.
- Canvas subset:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts')`
  - Passed: 75 tests.
- Frontend lint:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint`
  - Passed with 3 existing warnings.
- Docker stack:
  - `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'`
  - `ai-video-nginx`, `ai-video-frontend`, `ai-video-backend`, `ai-video-mysql`, `ai-video-redis`, `ai-video-celery-worker`, and `ai-video-celery-beat` were running.
  - `curl -fsS -o /tmp/ai-video-canvas-health.html -w '%{http_code}' http://localhost:8089/canvas || true`
  - Returned `200`.
- Real browser validation:
  - Chrome DevTools attempt failed with `Could not connect to Chrome... 127.0.0.1:9222/json/version: HTTP Not Found`.
  - Used the in-app browser fallback requested by the user.
  - Created run `800da67b06514d978e2841ae2512315a` through `http://localhost:8000/api/v1/production-canvas/plan`.
  - Saved duplicate persisted edges through `PUT /api/v1/production-canvas/runs/800da67b06514d978e2841ae2512315a/state`.
  - Opened `http://localhost:8089/canvas?run_id=800da67b06514d978e2841ae2512315a`.
  - Result: page showed `已恢复`, `[data-canvas-edge]` rendered one edge `brief-script`, `移除连线 Script` appeared once, and browser warn/error logs were empty.
  - Evidence: `artifacts/runs/2026-07-03T03-41-42Z-canvas-duplicate-edge-restore/in-app-browser-result.json`, `artifacts/runs/2026-07-03T03-41-42Z-canvas-duplicate-edge-restore/canvas-duplicate-edge-restore.png`.
- Full frontend tests:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test`
  - Passed: 205 tests.
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
