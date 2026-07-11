---
id: 2026-07-03T04-38-12Z-canvas-media-frame-index-parse
date: "2026-07-03T04:38:12Z"
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

继续完善无限画布功能。可以拉起 `dev_in_docker`，用内置浏览器检验。

## Goals

- Prevent malformed media frame-index tokens from being partially parsed into valid frame indexes.
- Keep valid comma, whitespace, Chinese comma, and Chinese enumeration separators working.
- Validate the media-control path in tests and the running `/canvas` UI.

## Changes

- Added a regression test for malformed media frame-index input such as `3abc`.
- Changed `ProductionCanvasMediaControls` to accept only whole non-negative integer tokens before de-duping frame indexes.

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v22.20.0/bin:/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasMediaControls.test.tsx` -> red first: `3abc` was parsed as frame index `3`.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v22.20.0/bin:/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasMediaControls.test.tsx` -> pass, 3 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v22.20.0/bin:/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -maxdepth 1 -type f \( -name 'productionCanvas*.test.tsx' -o -name 'productionCanvas*.test.ts' \) | sort)` -> pass, 81 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v22.20.0/bin:/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> pass with 0 errors and 3 existing warnings.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v22.20.0/bin:/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test $(find tests -type f \( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \) ! -name 'toastProvider.test.tsx' | sort)` -> pass, 206 tests.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas` returned HTTP 200.
- User path: opened `/canvas` in the in-app browser, logged in with the repository test account after redirect, created prompt-only run `975753874ef446a3a735c141b3a73824`, selected `skill-image-candidates`, and entered `1 3abc 2 2 -1` in `媒体帧索引`.
- Console: no `error` or `warning` entries after the media-control path.
- Network: `/canvas` route available; prompt-only run creation used the authenticated browser session and did not execute the media skill.
- Result: the UI normalized the input to `1, 2`, displayed `frame_indexes: 1, 2`, and did not display `frame_indexes: 1, 3, 2`.
- Evidence: `artifacts/runs/20260703-canvas-media-frame-index-parse/browser_flow.canvas_media_frame_index_parse.json` and `artifacts/runs/20260703-canvas-media-frame-index-parse/canvas-media-frame-index-parse.png`.

3. Conflict signals and corrections:

- Initial assumption: the default canvas `Image Candidates` node would expose media controls.
- Contradicting evidence: the default node is a pipeline node without `skill`, so the media controls were absent.
- Reproduction and fix: created a prompt-only canvas run so the restored graph included the blocked `skill-image-candidates` skill node without triggering media execution.
- Final verified state: malformed frame-index tokens are ignored in tests and in the running browser UI.

## Next Steps

- Continue the active infinite-canvas goal with the next small browser-verifiable workflow increment.
- The known unrelated full `npm run test` hang in `tests/toastProvider.test.tsx` remains outside this change.

## Linked Commits

- Not committed.
