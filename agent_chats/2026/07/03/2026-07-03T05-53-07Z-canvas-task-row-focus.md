---
id: "2026-07-03T05-53-07Z-canvas-task-row-focus"
date: "2026-07-03T05:53:07Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - frontend
  - browser-validation
summary: "Return focus to the canvas after selecting task evidence rows."
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasTaskSummary.tsx
  - ai-pic-frontend/tests/productionCanvasTaskSummary.test.tsx
  - artifacts/runs/20260703-canvas-task-row-focus/browser-evidence.json
  - artifacts/runs/20260703-canvas-task-row-focus/canvas-task-row-focus.png
---

## User Prompt

继续完善无限画布功能，保持原子化提交。用户允许拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Keep keyboard control on the infinite canvas after an operator clicks a task evidence row in the side panel.
- Match the existing focus-return behavior of task summary filter, expand, refresh, and toolbar actions.
- Keep the change scoped to the task summary component and its focused test.

## Changes

- Updated task evidence row clicks to call `onReturnFocus` after selecting the task node.
- Added a focused regression test covering row selection plus focus return.

## Validation

- TDD red: `tests/productionCanvasTaskSummary.test.tsx` failed because clicking `定位任务 8` selected the node but left `returnedFocus` at `0`.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasTaskSummary.test.tsx` passed, 2 tests.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvas*.test.tsx` passed, 86 tests.
- `cd ai-pic-frontend && npm run lint` completed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasTaskSummary.tsx ai-pic-frontend/tests/productionCanvasTaskSummary.test.tsx` passed.
- `docker compose -f docker/docker-compose.dev.yml ps` confirmed the dev stack was running, including nginx on `0.0.0.0:8089->8080`.
- `curl -I --max-time 5 http://localhost:8089/canvas` returned `HTTP/1.1 200 OK`.
- Chrome DevTools was unavailable: `list_pages` could not connect to `http://127.0.0.1:9222/json/version`, so browser validation used Playwright fallback.
- Playwright fallback path:
  - Entry URL: `http://localhost:8089/canvas?run_id=5f962649ec5841bfb56405564f62e967`
  - Login: `geyunfei`
  - Action: clicked `定位任务 102` in the task evidence summary.
  - After click: active element was the canvas region with `aria-label="短剧生产链路无限画布"`, `role="region"`, and `data-production-canvas="infinite-canvas"`.
  - Console warnings/errors: none.
- Browser artifacts:
  - `artifacts/runs/20260703-canvas-task-row-focus/browser-evidence.json`
  - `artifacts/runs/20260703-canvas-task-row-focus/canvas-task-row-focus.png`

## Next Steps

- Continue splitting the remaining canvas work into focused atomic commits.

## Linked Commits

- This commit.
