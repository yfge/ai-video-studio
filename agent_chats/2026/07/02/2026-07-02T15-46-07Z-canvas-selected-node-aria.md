---
id: 2026-07-02T15-46-07Z-canvas-selected-node-aria
date: "2026-07-02T15:46:07Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - delivery
related_paths:
  - ai-pic-frontend/src/components/features/canvas
  - ai-pic-frontend/tests
summary: Records one increment of the production infinite canvas implementation and its validation.
---

## User Prompt

/goal 继续完善无限画布功能

## Goals

- Expose the currently selected canvas node in the DOM for assistive technology and browser evidence.
- Preserve the existing visual selected-node ring and selection clearing behavior.

## Changes

- Updated `ProductionCanvasNodeCard.tsx` so selected nodes render `aria-current="true"`.
- Added a board regression proving the Script node gets `aria-current` when selected and loses it after `Escape`.
- Tightened the existing selection test to use `fireEvent.click` and tolerate the selected node text appearing in both the card and inspector.
- Split the pure canvas state/view-model regression into `productionCanvasState.test.ts` so the board render test stays under the repo file-size limit.

## Validation

- Focused passed: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasState.test.ts`
- Focused result: 7/7 tests passed across 2 suites.
- Initial focused test failed before the test fix because the old test used native `.click()` and then `getByText(...)` on text that appears in both the node card and inspector once selection really updates.
- Browser validation: Chrome DevTools transport returned `HTTP Not Found` for `http://127.0.0.1:9222/json/version`, so Playwright fallback was used and recorded.
- Browser evidence passed: `artifacts/runs/canvas-selected-node-aria-2026-07-02T15-46-59-655Z/browser_flow.canvas_selected_node_aria.json`
- Browser result: `selectedAfterClick` was `"true"`, `currentNodeCount` was `1`, `selectedAfterEscape` was `null`, `currentNodeCountAfterEscape` was `0`, with no failed requests or console problems.
- Full frontend tests passed: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` (164/164 tests).
- Frontend lint passed with existing warnings only: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` (0 errors, 3 warnings).
- Repo docs passed: `python scripts/check_repo_docs.py`.
- Repo contracts passed: `python scripts/check_repo_contracts.py --mode audit`.
- Scoped contract diff passed: `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasState.test.ts agent_chats/2026/07/02/2026-07-02T15-46-07Z-canvas-selected-node-aria.md`.
- Whitespace diff check passed: `git diff --check -- ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasState.test.ts agent_chats/2026/07/02/2026-07-02T15-46-07Z-canvas-selected-node-aria.md`.

## Next Steps

- Continue the next infinite-canvas increment under the active goal.

## Linked Commits

- Not committed.
