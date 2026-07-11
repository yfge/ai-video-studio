---
id: 2026-07-02T13-59-43Z-canvas-note-test-split
date: "2026-07-02T13:59:43Z"
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

- Stop adding note behavior coverage to the oversized `productionCanvasBoard.test.tsx`.
- Keep existing manual-note behavior covered without changing runtime canvas code.

## Changes

- Moved manual-note behavior tests into `tests/productionCanvasNotes.test.tsx`.
- Left `productionCanvasBoard.test.tsx` focused on board shell, keyboard, graph, task summary, and planner execution behavior for now.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx` - pass, 13 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasNotes.test.tsx` - pass, 4 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` - first aggregate run failed once in unrelated `toastProvider.test.tsx` auto-dismiss timing after all canvas tests passed.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/toastProvider.test.tsx` - pass, 5 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` - pass on rerun, 153 tests, 25 suites.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` - pass with existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` - pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasNotes.test.tsx` - no diff-sensitive rules were provided; skipped.
- `python scripts/check_repo_contracts.py --mode audit` - pass.
- `git diff --check -- ai-pic-frontend/tests/productionCanvasBoard.test.tsx ai-pic-frontend/tests/productionCanvasNotes.test.tsx` - pass.
- Browser evidence was not run because this increment only moved tests and did not change runtime app behavior.
- `npm run build` was not run because this increment did not touch routes, layout, config, auth, hydration, or runtime code.

## Next Steps

- Continue splitting `productionCanvasBoard.test.tsx`; it is improved from 1029 to 950 lines, but still exceeds the repository hard size target.

## Linked Commits

- Uncommitted.
