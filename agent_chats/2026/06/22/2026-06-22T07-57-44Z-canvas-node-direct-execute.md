---
id: 2026-06-22T07-57-44Z-canvas-node-direct-execute
date: 2026-06-22T07:57:44Z
participants:
  - user
  - codex
models:
  - GPT-5
tags:
  - frontend
  - production-canvas
  - validation
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasViewModel.ts
  - ai-pic-frontend/tests/productionCanvasBoard.test.tsx
summary: Added direct node-level execution controls for production canvas skill nodes.
---

## User Prompt

/goal 继续推进无限画布的功能

## Goals

- Continue the production canvas without creating a separate orchestration stack.
- Make planned skill nodes actionable directly on the infinite canvas, not only through the right inspector.
- Preserve existing drag, selection, fit, zoom, note, and dynamic task-evidence node behavior.

## Changes

- Added a node-level `后台执行` button for `skill_result` canvas nodes.
- Kept the card body as the selection/drag surface and isolated the execution button so it does not start canvas dragging.
- Increased default `skill_result` card height to make room for the node-level action.
- Split the node card into `ProductionCanvasNodeCard.tsx` after contract diff flagged `ProductionCanvasElements.tsx` as oversized.
- Updated the canvas behavior test so the first script execution is triggered from the canvas node button named `后台执行 Script Skill`.

## Validation

1. TDD red/green:

- Red phase: changed `ai-pic-frontend/tests/productionCanvasBoard.test.tsx` to require direct node execution via `后台执行 Script Skill`; the suite failed on the missing button as expected.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> pass, 5 tests passed.

2. Local checks:

- `cd ai-pic-frontend && npm run lint` -> pass with 0 errors and 3 pre-existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass; `/canvas` was included in the generated route list.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx ai-pic-frontend/src/components/features/canvas/productionCanvasViewModel.ts ai-pic-frontend/tests/productionCanvasBoard.test.tsx` -> pass.
- `git diff --check` -> pass.

3. Browser or MCP validation:

- Entry URL intended: `http://127.0.0.1:3000/canvas`.
- Chrome DevTools MCP: failed twice with `Failed to fetch browser webSocket URL from http://127.0.0.1:9222/json/version: HTTP Not Found`.
- Playwright bundled Chromium: blocked because the browser executable was not installed under `~/Library/Caches/ms-playwright/...`.
- Playwright with system Chrome: launched Chrome, but `browser.newPage` did not return and was interrupted.
- In-app browser fallback: local page opened, but its restricted evaluation sandbox could not set `window.localStorage`; `javascript:` token-setting navigation was rejected by browser security policy, so the auth-guarded `/canvas` path could not be completed without a running backend login flow.
- Result: no successful real-browser validation was claimed for this change.

4. Conflict signals and corrections:

- Initial implementation put the direct action into `ProductionCanvasElements.tsx`; contract diff rejected the file at 268 lines.
- Correction: split `CanvasNodeCard` into its own file and reran contract diff successfully.
- Initial direct-button pointer handler used `preventDefault()` on pointerdown; before browser work, this was narrowed to `stopPropagation()` to avoid interfering with native button click synthesis.

## Next Steps

- Run a real `/canvas` browser flow once the lite backend or AP stack is available, preferably through Chrome DevTools MCP.
- Consider adding a canvas-specific browser scenario that can log in and exercise `整体创建 -> node-level 后台执行 -> Task #...` evidence nodes.

## Linked Commits

- This commit: `feat(canvas): execute skill nodes from canvas`
