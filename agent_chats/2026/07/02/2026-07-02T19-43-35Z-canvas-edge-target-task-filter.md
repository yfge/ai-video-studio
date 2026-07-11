---
id: 2026-07-02T19-43-35Z-canvas-edge-target-task-filter
date: "2026-07-02T19:43:35Z"
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

Continue working toward the active thread goal.

## Goals

- Reduce noise in the infinite canvas side-panel edge editor for canvases with many task evidence nodes.
- Keep task evidence nodes available through the task summary, but remove them from the generic edge target dropdown.
- Preserve normal skill nodes as edge targets even when they carry a run-level `canvas_task_id`.

## Changes

- Updated `ProductionCanvasEdgeControls` to exclude only task evidence notes from edge targets: `kind === "note"` with a task output id.
- Added a regression test that keeps `Task #...` evidence nodes out of the edge target select while preserving normal notes and skill result nodes.

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> red before the fix when `Task #77` appeared in the edge target select.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> red again when the first filter hid `Report Skill` because it also had `canvas_task_id`.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> pass, 8 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasBusyActions.test.tsx tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPlanner.test.tsx` -> pass, 35 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> pass with 3 existing warnings: anonymous default export in `eslint.config.mjs`, and two existing `<img>` warnings in reference-image fields.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> pass, 183 tests.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas`.
- Environment: existing dev-in-docker stack through `ai-video-nginx` on `localhost:8089`.
- User path: reloaded `/canvas` in the in-app browser, kept the selected task evidence node `Task #6245 生产画布整体创建`, and inspected the `连线目标` select.
- Console: no browser `error` or `warning` log entries were captured for the path.
- Network: this is a local render-only filter; the route reload confirmed the updated dev-in-docker frontend surface.
- Result: `连线目标` had 12 options, `task_option_count=0`, while `Report Skill` and `Asset Selection` remained present.
- Evidence artifact: `artifacts/runs/2026-07-02T19-43-35Z-canvas-edge-target-task-filter/in-app-browser-result.json`.

3. Conflict signals and corrections:

- Initial assumption: filtering by `taskOutputNumber(outputs)` would only remove task evidence nodes.
- Contradicting evidence: browser validation showed the select collapsed to `所有目标已连线` because normal plan/skill nodes also carry run-level `canvas_task_id`.
- Reproduction and fix: added a failing assertion that `Report Skill` remains an option even when it has `canvas_task_id`; narrowed the filter to `kind === "note"` plus task output.
- Final verified state: task evidence nodes are hidden from edge targets, normal skill targets remain selectable, and local/browser validation passed.

## Next Steps

- Continue with the next small infinite-canvas workflow increment.
- `npm run build` was not run because this change is client-side component behavior only, not route, layout, auth, config, or hydration-sensitive code.
- No files were staged or committed; unrelated existing worktree changes were left untouched.

## Linked Commits

- Not committed in this turn.
