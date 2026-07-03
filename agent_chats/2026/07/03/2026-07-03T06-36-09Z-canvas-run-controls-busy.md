## User Prompt

继续完善无限画布功能。用户允许拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Expose RunControls save/restore busy state to assistive technology.
- Prevent editing Run ID while save/restore work is busy.
- Keep this slice separate from larger copy-link RunControls work.

## Changes

- Added `aria-busy` to the save and restore buttons when RunControls are busy.
- Disabled the Run ID input while RunControls are busy.
- Added focused RunControls coverage for busy controls.

## Validation

- TDD red: clean HEAD with the current RunControls test failed; the busy test saw `aria-busy` as `null` instead of `"true"`, and the copied broader test also confirmed copy-link work is outside this slice.
- Clean staged-patch worktree: `PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasRunControls.test.tsx` passed, 1 test.
- Clean staged-patch worktree: `python scripts/check_repo_docs.py` passed.
- Clean staged-patch worktree: `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx ai-pic-frontend/tests/productionCanvasRunControls.test.tsx agent_chats/2026/07/03/2026-07-03T06-36-09Z-canvas-run-controls-busy.md` passed.
- Clean staged-patch worktree: `cd ai-pic-frontend && npm run lint` completed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- Clean staged-patch worktree: `pre-commit run --files ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx ai-pic-frontend/tests/productionCanvasRunControls.test.tsx agent_chats/2026/07/03/2026-07-03T06-36-09Z-canvas-run-controls-busy.md` passed.
- Chrome DevTools MCP fallback recorded: `mcp__chrome_devtools.list_pages` could not fetch `http://127.0.0.1:9222/json/version` and returned HTTP 404.
- Dev docker browser path:
  - Entry URL: `http://localhost:8089/canvas`.
  - Auth: dev API login token seeded into browser localStorage, token redacted from evidence.
  - User path: enter `canvas-run-busy`, click `保存画布`, and hold the save-state request open.
  - Assertions: save-state request intercepted; save and restore buttons both had `aria-busy="true"`; Run ID input was disabled; `保存中` was visible.
  - Console warnings/errors: none.
  - Failed requests: none.
- Browser artifacts:
  - `artifacts/runs/20260703-canvas-run-controls-busy/browser-evidence.json`
  - `artifacts/runs/20260703-canvas-run-controls-busy/canvas-run-controls-busy.png`

## Next Steps

- Continue with the next small infinite-canvas interaction increment.

## Linked Commits

- Not committed.
