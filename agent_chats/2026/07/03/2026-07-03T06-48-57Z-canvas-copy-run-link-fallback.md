---
id: 2026-07-03T06-48-57Z-canvas-copy-run-link-fallback
date: "2026-07-03T06:48:57Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - run-controls
summary: Added copy-run-link controls with browser fallback status.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx
  - ai-pic-frontend/tests/productionCanvasRunControls.test.tsx
---

## User Prompt

/goal 继续完善无限画布功能

User also asked to use the dev Docker stack and in-app browser when useful.

## Goals

- Add a small RunControls affordance for sharing/restoring a canvas run by link.
- Keep the commit scoped to the run controls and its focused tests.
- Verify the user-visible path in the local dev Docker browser flow.

## Changes

- Added a `复制链接` action next to `复制 Run ID`.
- Built restore links as `/canvas?run_id=<run id>` from the current browser origin.
- Added a local clipboard helper that tries `navigator.clipboard.writeText`, then a DOM copy fallback when available.
- When the browser exposes no copy primitive, the status region now shows the generated restore link instead of only saying copy failed.
- Relaxed the status region height so long fallback links can wrap instead of overflowing.
- Covered both the DOM fallback path and the no-copy-primitive fallback in `productionCanvasRunControls.test.tsx`.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasRunControls.test.tsx` -> pass, 5 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx ai-pic-frontend/tests/productionCanvasRunControls.test.tsx` -> pass.
- `git diff --cached --check` -> pass.
- `pre-commit run --files ai-pic-frontend/src/components/features/canvas/ProductionCanvasRunControls.tsx ai-pic-frontend/tests/productionCanvasRunControls.test.tsx agent_chats/2026/07/03/2026-07-03T06-48-57Z-canvas-copy-run-link-fallback.md` -> pass.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas` on the dev Docker stack.
- User path: logged in with the repo test account, opened `/canvas`, filled Run ID `canvas-copy-link-e2e`, clicked `复制链接`.
- Console: no warn/error entries from the browser log capture.
- Network: no network request is required for this local copy/share action.
- Result: in-app browser exposed no page clipboard primitive, so clipboard remained empty; the visible status region showed `复制失败，链接已生成：http://localhost:8089/canvas?run_id=canvas-copy-link-e2e`.
- Evidence: `artifacts/runs/20260703-canvas-copy-run-link-fallback/browser-evidence.json`, `artifacts/runs/20260703-canvas-copy-run-link-fallback/canvas-copy-run-link-fallback.png`.

3. Conflict signals and corrections:

- Initial assumption: `navigator.clipboard.writeText` would be enough for the browser path.
- Contradicting evidence: the in-app browser showed `复制失败` and an empty clipboard after clicking `复制链接`.
- Reproduction and fix: added DOM fallback, then found the in-app browser also lacks `document.execCommand`; added a no-copy-primitive branch that displays the generated restore link.
- Final verified state: the control provides the restore URL in the live status region when automatic copy is unavailable.

## Next Steps

- Continue with the remaining RunControls increments as separate commits, such as Enter-to-restore and focus return.
- Keep Board-level keyboard, note, edge, and task-sync work in separate slices.

## Linked Commits

- pending
