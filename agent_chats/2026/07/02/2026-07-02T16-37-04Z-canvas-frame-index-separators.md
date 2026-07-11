---
id: 2026-07-02T16-37-04Z-canvas-frame-index-separators
date: "2026-07-02T16:37:04Z"
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

- Make canvas media frame-index inputs tolerate common operator separators.
- Keep the increment scoped to the existing media controls and media-control test.

## Changes

- Updated `parseFrameIndexes` to split on English commas, Chinese commas, ideographic commas, and whitespace.
- Extended media-control coverage so image and video frame indexes entered with mixed separators still execute as `[1, 2]`.

## Validation

- `wc -l ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx ai-pic-frontend/tests/productionCanvasMediaControls.test.tsx ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts`
  - Media controls: 152 lines.
  - Media controls test: 172 lines.
  - Board/controller/state left untouched at 249/250/250 lines.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasMediaControls.test.tsx`
  - Passed: 1 test.
- Chrome DevTools validation attempted twice.
  - Failed both times: `Failed to fetch browser webSocket URL from http://127.0.0.1:9222/json/version: HTTP Not Found`.
- Playwright fallback browser validation:
  - Entry URL: `http://127.0.0.1:3000/canvas`.
  - Auth: seeded `localStorage.auth_token` and `user_info`.
  - Backend: route-mocked `POST /api/v1/production-canvas/plan` to return one dynamic `image.candidates` node because the default static Image node is not a media skill node.
  - User path: entered `生成图片候选`, clicked `整体创建`, selected `skill-image-candidates`, and filled `媒体帧索引` with `1， 2 2`.
  - Result: input normalized to `1, 2`; inspector output showed `frame_indexes: 1, 2`.
  - Artifacts: `artifacts/runs/20260702T163633Z-canvas-frame-index-separators/canvas-frame-index-separators.json`, `artifacts/runs/20260702T163633Z-canvas-frame-index-separators/canvas-frame-index-separators.png`.
  - Console errors: none.
  - Failed requests: none.
  - Corrections: first fallback used stale Image node aria text; second used the static Image node, which correctly exposed no media controls. Final run used a route-mocked dynamic media skill node.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test`
  - Passed: 166 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint`
  - Passed with 3 existing warnings.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode audit`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx ai-pic-frontend/tests/productionCanvasMediaControls.test.tsx agent_chats/2026/07/02/2026-07-02T16-37-04Z-canvas-frame-index-separators.md`
  - Passed.
- `git diff --check -- ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx ai-pic-frontend/tests/productionCanvasMediaControls.test.tsx`
  - Passed.
- `git diff --check --no-index /dev/null agent_chats/2026/07/02/2026-07-02T16-37-04Z-canvas-frame-index-separators.md`
  - Passed with no whitespace warnings.
- `npm run build` skipped because this was client component parser behavior only, with no route, layout, auth, config, SSR, or hydration-sensitive change.

## Next Steps

- Continue shipping concrete canvas usability increments under the active infinite canvas goal.

## Linked Commits

- Pending commit.
