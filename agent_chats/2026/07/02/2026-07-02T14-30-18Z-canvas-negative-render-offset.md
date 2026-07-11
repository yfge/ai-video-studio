---
id: 2026-07-02T14-30-18Z-canvas-negative-render-offset
date: "2026-07-02T14:30:18Z"
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

`/goal 继续完善无限画布功能`

## Goals

- Keep the production canvas usable when nodes move into negative world coordinates.
- Ensure Home/fit view, rendered node positions, and SVG edges stay aligned after the canvas world expands left or upward.
- Record focused automated and browser evidence for the user-visible canvas behavior.

## Changes

- Offset rendered canvas nodes by the world bounds minimum coordinate while preserving their stored world coordinates.
- Offset SVG edge paths with the same world bounds transform so edges continue to connect to their rendered nodes.
- Added a keyboard regression assertion for a Script node nudged to negative X, including the rendered `script-storyboard` edge path.
- Hardened the canvas persistence test to wait for asynchronous URL sync after a Run ID is created.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasKeyboard.test.tsx tests/productionCanvasBoard.test.tsx tests/productionCanvasGraph.test.tsx` passed: 11 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPersistence.test.tsx` passed: 5 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/toastProvider.test.tsx` passed: 5 tests after an initial full-suite timing failure.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` passed: 154 tests, 28 suites.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` passed with existing warnings only in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode audit` passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx ai-pic-frontend/src/components/features/canvas/productionCanvasViewModel.ts ai-pic-frontend/src/components/features/canvas/useProductionCanvasInteractionControls.ts ai-pic-frontend/tests/productionCanvasKeyboard.test.tsx ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasGraph.test.tsx ai-pic-frontend/tests/productionCanvasPersistence.test.tsx` passed.
- `git diff --check -- ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx ai-pic-frontend/src/components/features/canvas/productionCanvasViewModel.ts ai-pic-frontend/src/components/features/canvas/useProductionCanvasInteractionControls.ts ai-pic-frontend/tests/productionCanvasKeyboard.test.tsx ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasGraph.test.tsx ai-pic-frontend/tests/productionCanvasPersistence.test.tsx` passed.
- Chrome DevTools browser validation was attempted first and failed with `Failed to fetch browser webSocket URL from http://127.0.0.1:9222/json/version: HTTP Not Found`.
- Playwright Chromium fallback passed for `/canvas`: selected `script`, nudged it to X `-50`, pressed Home, and verified rendered Script left `0px`, world left `-50px`, width `1310px`, and edge path `M 190 107 C 380 107 380 107 570 107`.
- Browser evidence was written to `artifacts/runs/canvas-negative-render-offset-2026-07-02T14-29-24Z/browser_flow.canvas_negative_render.json` and `artifacts/runs/canvas-negative-render-offset-2026-07-02T14-29-24Z/screenshot.png`.
- `npm run build` was not run because this change is limited to client canvas rendering, hooks, and tests, with no route, layout, auth, config, SSR, or hydration-sensitive surface changed.

## Next Steps

- Continue expanding canvas behavior in small increments, keeping negative-coordinate and browser evidence in the loop.
- Consider a dedicated browser scenario script under `scripts/harness/` once the canvas interaction set stabilizes.

## Linked Commits

- Not committed in this turn.
