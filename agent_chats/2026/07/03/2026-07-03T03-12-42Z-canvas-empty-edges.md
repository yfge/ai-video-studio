---
id: "2026-07-03T03-12-42Z-canvas-empty-edges"
date: "2026-07-03T03:12:42Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - browser-validation
summary: "Preserve empty local canvas edge lists after reload."
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasViewModel.ts
  - ai-pic-frontend/tests/productionCanvasPersistence.test.tsx
  - artifacts/runs/2026-07-03T03-12-42Z-canvas-empty-edges/in-app-browser-result.json
---

## User Prompt

- Continue improving the infinite canvas feature.
- The dev_in_docker stack and built-in browser are available for validation.

## Goals

- Preserve deliberate deletion of all canvas edges in local saved state.
- Prevent a page reload from restoring default canvas edges when `edges: []` is the saved value.

## Changes

- Updated local saved-state edge restore to treat an empty edge array as valid saved state.
- Added a regression test that stores `edges: []` and expects `readStoredCanvasState(...)` to restore an empty edge list.

## Validation

- Red check: `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPersistence.test.tsx` failed before the fix because `edges: []` restored the default 7 edges.
- Green check: the same focused command passed after the fix with 7/7 tests passing.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` passed with 0 errors and 3 existing warnings.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` passed with 205/205 tests passing.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode audit` passed.
- `curl http://localhost:8089/canvas` returned HTTP 200.
- In-app browser validation opened `http://localhost:8089/canvas`, clicked `重置`, removed the seven default edges through the edge editor, reloaded `/canvas`, and confirmed rendered edge count stayed `0`.
- Browser logs had 0 errors and 0 warnings; only React DevTools, HMR, and Fast Refresh development logs were present.

## Next Steps

- Continue with the next narrow canvas workflow gap.

## Linked Commits

- Uncommitted local work.
