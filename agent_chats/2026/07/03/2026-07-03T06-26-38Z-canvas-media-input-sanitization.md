## User Prompt

继续完善无限画布功能。用户允许拉起 dev_in_docker 并用内置浏览器检验。

## Goals

- Make media execution controls tolerate common frame-index separators from Chinese and space-separated input.
- Ignore malformed frame-index tokens without losing later valid indexes.
- Drop non-positive video numeric parameters instead of sending invalid `0` or negative values.

## Changes

- Updated media frame-index parsing to split on comma, Chinese comma, enumeration comma, and whitespace.
- Kept only unsigned integer frame-index tokens and de-duplicated them.
- Updated numeric parsing so video duration/FPS must be positive finite numbers.
- Added focused media control regression coverage for separators, malformed frame tokens, and non-positive video numbers.

## Validation

- TDD red: test-only patch in a clean HEAD worktree failed because `frame_indexes: 1, 2` was not rendered, `duration: 0` and `fps: -24` were preserved, and malformed frame input kept only `[1]`.
- Clean staged-patch worktree: `PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasMediaControls.test.tsx` passed, 3 tests.
- Clean staged-patch worktree: `python scripts/check_repo_docs.py` passed.
- Clean staged-patch worktree: `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx ai-pic-frontend/tests/productionCanvasMediaControls.test.tsx agent_chats/2026/07/03/2026-07-03T06-26-38Z-canvas-media-input-sanitization.md` passed.
- Clean staged-patch worktree: `cd ai-pic-frontend && npm run lint` completed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- Clean staged-patch worktree: `pre-commit run --files ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx ai-pic-frontend/tests/productionCanvasMediaControls.test.tsx agent_chats/2026/07/03/2026-07-03T06-26-38Z-canvas-media-input-sanitization.md` passed after formatting the two media files with the prettier hook.
- Chrome DevTools MCP fallback recorded: `mcp__chrome_devtools.list_pages` could not fetch `http://127.0.0.1:9222/json/version` and returned HTTP 404.
- Dev docker browser path:
  - Stack was already running through `docker/docker-compose.dev.yml`, with `/canvas` served at `http://localhost:8089/canvas`.
  - Auth: dev API login token seeded into browser localStorage, token redacted from evidence.
  - Seeded `image.candidates` and `video.candidates` nodes under `production-canvas-layout-v1`.
  - User path: enter image frame indexes `1， 2 2 -1 3abc`, then enter video duration `0`, FPS `-24`, duration `6`, FPS `30`, and frame indexes `1、2 2`.
  - Assertions: image and video output showed `frame_indexes: 1, 2`; non-positive video inputs reset to empty and did not render `duration: 0` or `fps: -24`; valid `duration: 6` and `fps: 30` rendered.
  - Console warnings/errors: none.
  - Failed requests: none.
- Browser artifacts:
  - `artifacts/runs/20260703-canvas-media-input-sanitization/browser-evidence.json`
  - `artifacts/runs/20260703-canvas-media-input-sanitization/canvas-media-input-sanitization.png`

## Next Steps

- Continue with the next small infinite-canvas interaction increment.

## Linked Commits

- Not committed.
