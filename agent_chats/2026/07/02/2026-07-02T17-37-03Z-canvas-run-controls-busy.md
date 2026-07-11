---
id: 2026-07-02T17-37-03Z-canvas-run-controls-busy
date: "2026-07-02T17:37:03Z"
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

继续完善无限画布功能

## Goals

- Make canvas run save/restore busy state machine-readable.
- Keep Run ID editing locked while a save or restore is in progress.

## Changes

- Added `aria-busy` to the run save and restore buttons while persistence is busy.
- Disabled the Run ID input while persistence is busy, so Enter cannot trigger another restore during an in-flight save or restore.
- Added focused RunControls coverage for the busy state.

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasRunControls.test.tsx` -> passed, 2 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> passed, 172 tests / 31 suites.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> passed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode audit` -> passed.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas?run_id=b397f16b0ccc4147a7f2824dda7ef442`
- Environment: `docker/dev_in_docker.sh` stack through nginx on port 8089.
- User path: open the saved canvas run, log in if redirected, click `恢复画布`, sample DOM while restore is in progress, and wait until restore completes.
- Busy state: sampled `保存画布` and `恢复画布` with `aria-busy="true"`, Run ID input disabled, and status `恢复中`.
- Final state: `aria-busy` removed, Run ID input enabled, and status `已恢复`.
- Console: no warning/error logs.
- Result: passed. Evidence saved under `artifacts/runs/20260702T173703Z-canvas-run-controls-busy/in-app-browser-result.json`.

3. Conflict signals and corrections:

- Initial browser sampling awaited the click before reading DOM and only saw the final `已恢复` state.
- Corrected by sampling immediately after dispatching the restore click and before awaiting completion.

## Next Steps

- Continue improving the infinite canvas in small user-facing increments.
- Run production build and Docker image checks before any commit or push.

## Linked Commits

- Uncommitted.
