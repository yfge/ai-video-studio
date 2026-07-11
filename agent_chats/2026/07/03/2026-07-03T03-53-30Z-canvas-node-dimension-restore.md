---
id: "2026-07-03T03-53-30Z-canvas-node-dimension-restore"
date: "2026-07-03T03:53:30Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
  - browser-validation
summary: "Normalize restored production canvas node dimensions."
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - artifacts/runs/2026-07-03T03-52-44Z-canvas-node-dimension-restore/in-app-browser-result.json
---

## User Prompt

/goal 继续完善无限画布功能

用户补充：可以拉起 dev_in_docker，用内置浏览器检验。

## Goals

- Prevent restored canvas nodes with bad persisted dimensions from collapsing in the infinite canvas.
- Validate through unit coverage and a real Docker-backed browser restore path.

## Changes

- Normalized restored node dimensions in `createProductionCanvasState`: non-positive widths fall back to `190`, and invalid or non-positive heights are cleared so existing height fallback logic applies.
- Added state test coverage for restoring a node with `width: 0` and negative `height`.

## Validation

- Red check before implementation:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Failed because restored node width remained `0`.
- Green focused state check:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasState.test.ts`
  - Passed: 3 tests.
- File size:
  - `wc -l ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts ai-pic-frontend/tests/productionCanvasState.test.ts`
  - State file remained 249 lines.
- Canvas subset:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts')`
  - Passed: 77 tests.
- Frontend lint:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint`
  - Passed with 3 existing warnings.
- Docker stack:
  - `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | rg 'ai-video|NAMES'`
  - `ai-video-nginx`, `ai-video-frontend`, `ai-video-backend`, `ai-video-mysql`, `ai-video-redis`, `ai-video-celery-worker`, and `ai-video-celery-beat` were running.
  - `curl -fsS -o /tmp/ai-video-canvas-health.html -w '%{http_code}' http://localhost:8089/canvas || true`
  - Returned `200`.
- Real browser validation:
  - Chrome DevTools attempt failed with `Could not connect to Chrome... 127.0.0.1:9222/json/version: HTTP Not Found`.
  - Used the in-app browser fallback requested by the user.
  - Created run `b70fef20b60e4946a80bf8e1b3100998` through `http://localhost:8000/api/v1/production-canvas/plan`.
  - Saved `brief` with `width: 0` and `height: -12` through `PUT /api/v1/production-canvas/runs/b70fef20b60e4946a80bf8e1b3100998/state`.
  - Opened `http://localhost:8089/canvas?run_id=b70fef20b60e4946a80bf8e1b3100998`.
  - Result: page showed `已恢复`, `brief` rendered at `190px x 118px`, edge `brief-script` rendered, and browser warn/error logs were empty.
  - Evidence: `artifacts/runs/2026-07-03T03-52-44Z-canvas-node-dimension-restore/in-app-browser-result.json`, `artifacts/runs/2026-07-03T03-52-44Z-canvas-node-dimension-restore/canvas-node-dimension-restore.png`.
- Full frontend tests:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test`
  - Passed: 207 tests.
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
