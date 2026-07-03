## User Prompt

继续完善无限画布功能。用户允许拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Let task summary rows select the matching task evidence node on the canvas.
- Keep the change scoped to the existing task summary callback contract.
- Verify with a failing regression test first and a browser-visible `/canvas` path.

## Changes

- Added a board-level regression test that seeds task evidence in localStorage, clicks a task summary row, and expects the task node to show the canvas selected state.
- Wired `ProductionCanvasBoard` to pass the controller node-selection callback into `ProductionCanvasNodeTools`.

## Validation

- TDD red: `node --import tsx --test tests/productionCanvasBoardTaskSummary.test.tsx` failed in a clean HEAD worktree because the task node class did not include `ring-blue-500` after clicking `定位任务 909`.
- Clean staged-patch worktree: `PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasBoardTaskSummary.test.tsx tests/productionCanvasNodeTools.test.tsx tests/productionCanvasTaskSummary.test.tsx` passed, 5 tests.
- Clean staged-patch worktree: `python scripts/check_repo_docs.py` passed.
- Clean staged-patch worktree: `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/tests/productionCanvasBoardTaskSummary.test.tsx agent_chats/2026/07/03/2026-07-03T06-19-17Z-canvas-task-summary-select-node.md` passed.
- Clean staged-patch worktree: `cd ai-pic-frontend && npm run lint` completed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- Clean staged-patch worktree: `pre-commit run --files ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/tests/productionCanvasBoardTaskSummary.test.tsx agent_chats/2026/07/03/2026-07-03T06-19-17Z-canvas-task-summary-select-node.md` passed.
- Chrome DevTools MCP fallback recorded: `mcp__chrome_devtools.list_pages` could not fetch `http://127.0.0.1:9222/json/version` and returned HTTP 404.
- Dev docker browser path:
  - Stack: `docker compose -f docker/docker-compose.dev.yml ps` showed `ai-video-nginx`, `ai-video-frontend`, and `ai-video-backend` running.
  - Entry URL: `http://localhost:8089/canvas`.
  - Auth: dev API login token seeded into browser localStorage, token redacted from evidence.
  - Seeded canvas state under `production-canvas-layout-v1` with a `task-909` task evidence note.
  - User path: click task summary row `定位任务 909`.
  - Assertion: task node class changed from no selected ring to `ring-2 ring-blue-500 ring-offset-2`.
  - Console warnings/errors: none.
  - Failed requests: none.
- Browser artifacts:
  - `artifacts/runs/20260703-canvas-task-summary-select-node/browser-evidence.json`
  - `artifacts/runs/20260703-canvas-task-summary-select-node/canvas-task-summary-select-node.png`

## Next Steps

- Continue with the next small infinite-canvas interaction increment.

## Linked Commits

- Not committed.
