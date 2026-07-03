## User Prompt

继续完善无限画布功能。用户允许拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Make canvas creation errors announceable to assistive technology.
- Expose whole-canvas creation busy state on the create button.
- Keep numeric context ID fields numeric before they reach planner state.

## Changes

- Added `role="alert"` to the canvas creation error message.
- Added `aria-busy` to the whole-canvas create button while creation is running.
- Sanitized context ID input callbacks to digits only.
- Added focused ChatBar tests for alert, busy state, and numeric context input.

## Validation

- TDD red: copying only `productionCanvasChatBar.test.tsx` into a clean HEAD worktree failed because the error lacked role `alert`, the busy create button lacked `aria-busy="true"`, and `剧集 ID` emitted `12a-3` instead of `123`.
- Clean staged-patch worktree: `PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasChatBar.test.tsx` passed, 3 tests.
- Clean staged-patch worktree: `python scripts/check_repo_docs.py` passed.
- Clean staged-patch worktree: `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasChatBar.tsx ai-pic-frontend/tests/productionCanvasChatBar.test.tsx agent_chats/2026/07/03/2026-07-03T06-30-52Z-canvas-chatbar-input-accessibility.md` passed.
- Clean staged-patch worktree: `cd ai-pic-frontend && npm run lint` completed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- Clean staged-patch worktree: `pre-commit run --files ai-pic-frontend/src/components/features/canvas/ProductionCanvasChatBar.tsx ai-pic-frontend/tests/productionCanvasChatBar.test.tsx agent_chats/2026/07/03/2026-07-03T06-30-52Z-canvas-chatbar-input-accessibility.md` passed after formatting `ProductionCanvasChatBar.tsx` with the prettier hook.
- Chrome DevTools MCP fallback recorded: `mcp__chrome_devtools.list_pages` could not fetch `http://127.0.0.1:9222/json/version` and returned HTTP 404.
- Dev docker browser path:
  - Entry URL: `http://localhost:8089/canvas`.
  - Auth: dev API login token seeded into browser localStorage, token redacted from evidence.
  - User path: enter `12a-3` into `剧集 ID`.
  - Assertion: visible `剧集 ID` input value became `123`.
  - Console warnings/errors: none.
  - Failed requests: none.
- Browser artifacts:
  - `artifacts/runs/20260703-canvas-chatbar-input-accessibility/browser-evidence.json`
  - `artifacts/runs/20260703-canvas-chatbar-input-accessibility/canvas-chatbar-input-accessibility.png`

## Next Steps

- Continue with the next small infinite-canvas interaction increment.

## Linked Commits

- Not committed.
