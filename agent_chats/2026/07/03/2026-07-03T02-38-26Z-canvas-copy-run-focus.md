---
id: "2026-07-03T02-38-26Z-canvas-copy-run-focus"
date: "2026-07-03T02:38:26Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - browser-validation
summary: Return keyboard focus to the infinite canvas after run copy actions.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/tests/productionCanvasPlanner.test.tsx
  - artifacts/runs/2026-07-03T02-38-26Z-canvas-copy-run-focus/in-app-browser-result.json
---

## User Prompt

/goal 继续完善无限画布功能

你可以拉起 dev_in_docker 用内置浏览器检验

## Goals

- Keep the infinite canvas keyboard flow usable after toolbar copy actions.
- Cover the regression with a focused frontend test.
- Validate the behavior in the running dev Docker stack with the Codex in-app browser.

## Changes

- Added an optional `onReturnFocus` callback to `ProductionCanvasRunControls`.
- Returned focus to the canvas after both `复制 Run ID` and `复制链接`, including clipboard failure paths.
- Wired the canvas board to pass `canvasRef.current?.focus({ preventScroll: true })` into run controls.
- Added a planner regression test that creates a run, clicks `复制 Run ID`, and confirms `ArrowRight` still nudges the selected canvas node.
- Recorded browser evidence in `artifacts/runs/2026-07-03T02-38-26Z-canvas-copy-run-focus/in-app-browser-result.json`.

## Validation

- TDD red:
  - Temporarily removed the production focus return and ran `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx`.
  - The new subtest failed because `document.activeElement` stayed on the `复制 Run ID` button instead of the canvas.
- Focused green:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx` passed 10/10.
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasKeyboard.test.tsx` passed 16/16.
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasRunControls.test.tsx` passed 2/2.
- Broader frontend:
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` passed with 0 errors and 3 existing warnings.
  - `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` passed 201/201.
- Repo checks:
  - `python scripts/check_repo_docs.py` passed.
  - `python scripts/check_repo_contracts.py --mode audit` passed.
- Dev Docker and browser:
  - `docker compose -f docker/docker-compose.dev.yml ps` showed `ai-video-nginx`, `ai-video-frontend`, `ai-video-backend`, MySQL, Redis, Celery worker, and Celery beat running.
  - `curl http://localhost:8000/health` returned 200.
  - `curl http://localhost:8089/canvas` returned 200.
  - Created run `e50de054ff594d308bf7807998f98dda` with task `6256` through `POST /api/v1/production-canvas/plan`.
  - In the Codex in-app browser, logged in as the repository test account and opened `http://localhost:8089/canvas?run_id=e50de054ff594d308bf7807998f98dda`.
  - The page restored 10 nodes and selected `skill-brief-compose`.
  - Clicking `复制 Run ID` hit the clipboard failure branch in the browser, returned focus to `div[data-production-canvas='infinite-canvas']`, and `ArrowRight` moved the node from `80px` to `96px`.
  - Clicking `复制链接` also returned focus to the canvas, and `ArrowRight` moved the node from `96px` to `112px`.
  - Browser console warn/error log count was 0.
  - `GET /api/v1/production-canvas/runs/e50de054ff594d308bf7807998f98dda` showed `saved_state.nodes[].x = 112` for `skill-brief-compose`.

## Next Steps

- Continue the infinite canvas backlog with the next smallest interaction improvement.
- `pre-commit run --all-files` and `./docker/build_prod_images.sh` were not run in this increment.

## Linked Commits

- Not committed.
