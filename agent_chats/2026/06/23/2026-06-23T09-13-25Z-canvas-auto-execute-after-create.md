## User Prompt

我试了下创建一个画布以后就不执行了，和预期不符吧？

## Goals

- 确认“整体创建”是否应该在创建画布节点后继续执行 ready 节点。
- 修复前端只调用 `/production-canvas/plan`、不自动调用 `/production-canvas/execute` 的行为。
- 保留图片和视频候选节点的手动执行入口，避免跳过用户可调媒体参数。
- 用单测和浏览器证据证明点击“整体创建”后会继续执行。

## Changes

- Added automatic execution of ready, fully-satisfied skill nodes after whole-canvas creation.
- Reused the existing skill execution request mapping for both automatic execution and manual node execution.
- Reapplied canvas context after each automatic execution result so downstream nodes can become ready during the same overall creation flow.
- Skipped automatic execution for `image.candidates` and `video.candidates`, because those nodes expose frame indexes, model, aspect ratio, duration, FPS, reference-image, resolution, ratio, and camera controls that should remain user-tunable.
- Added a focused frontend regression test proving `整体创建` now triggers `/production-canvas/execute` for ready nodes.
- Updated the dynamic canvas execution test to expect the new automatic execution chain instead of manual button clicks for ready nodes.

## Validation

- RED before the fix: `cd ai-pic-frontend && npx tsx --test --test-name-pattern "automatically executes ready skill nodes" tests/productionCanvasBoard.test.tsx` failed because no `/production-canvas/execute` request was made.
- GREEN focused test after the fix: `cd ai-pic-frontend && npx tsx --test --test-name-pattern "automatically executes ready skill nodes" tests/productionCanvasBoard.test.tsx` passed.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasPersistence.test.tsx tests/productionCanvasMediaControls.test.tsx` passed with 10 tests.
- Browser validation against `http://localhost:9229/canvas` passed using Playwright driving system Google Chrome after Chrome DevTools/CDP launch timed out on this host.
- Browser evidence: `artifacts/runs/canvas-auto-execute-20260623T090450Z/browser_flow.canvas_auto_execute.json`.
- Browser network evidence: `artifacts/runs/canvas-auto-execute-20260623T090450Z/network.canvas_auto_execute.json`.
- Browser screenshot: `artifacts/runs/canvas-auto-execute-20260623T090450Z/screenshots/canvas-auto-execute.png`.
- Browser result captured 1 `/api/v1/production-canvas/plan` request and 2 `/api/v1/production-canvas/execute` requests after clicking `整体创建`: `brief.compose` and `report.summarize`.
- `cd ai-pic-frontend && npm run lint` passed with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts ai-pic-frontend/tests/productionCanvasBoard.test.tsx agent_chats/2026/06/23/2026-06-23T09-13-25Z-canvas-auto-execute-after-create.md` passed.
- `git diff --check` passed.
- `cd ai-pic-frontend && npm run test` ran the full frontend suite: 133 passed, 1 failed. The failure was `tests/toastProvider.test.tsx`, which hung for about 275 seconds after its first test; this is outside the canvas files changed here.
- `cd ai-pic-frontend && npx tsx --test tests/toastProvider.test.tsx` was rerun separately and also hung after the first test, so it was terminated with Ctrl-C.

## Next Steps

- If the whole-canvas product expectation is to execute media candidate generation immediately too, add an explicit confirmation step or default parameter profile before enabling auto-run for `image.candidates` and `video.candidates`.
- Investigate `tests/toastProvider.test.tsx` separately; it appears to leave timers or handles open and can make the full frontend test command fail despite passing assertions.

## Linked Commits

- This commit - `fix(canvas): auto-run ready nodes after creation`.
