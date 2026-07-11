---
id: 2026-07-02T19-50-08Z-canvas-task-evidence-edge-hide
date: "2026-07-02T19:50:08Z"
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

The user also said dev_in_docker and the built-in browser could be used for validation.

## Goals

- Remove the generic edge editor from selected task evidence nodes on the infinite canvas.
- Keep task evidence available through the task summary and inspector content.
- Preserve normal edge editing for non-task-evidence canvas nodes.

## Changes

- Updated `ProductionCanvasEdgeControls` to return no controls when the selected node is a task evidence note: `kind === "note"` with a task output id.
- Added a regression test that selected task evidence nodes do not render `连线编辑`.

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> red before the fix; `hides edge controls for task evidence nodes` found the edge controls.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasGraph.test.tsx` -> pass, 9 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasBusyActions.test.tsx tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPlanner.test.tsx` -> pass, 36 tests.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> pass with 3 existing warnings: anonymous default export in `eslint.config.mjs`, and two existing `<img>` warnings in reference-image fields.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> pass, 184 tests.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas?run_id=567b0cefc948467988f463e251e2b3b3`.
- Environment: existing dev-in-docker stack through `localhost:8089`, verified in the Codex in-app browser.
- User path: reloaded `/canvas`, kept the restored selected task evidence node `Task #6245 生产画布整体创建`, and inspected the selected-node side panel state.
- DOM evidence: selected button was `Task #6245待选择生产画布整体创建`; `has_task_evidence_text=true`; `has_edge_editor_text=false`; `edge_target_select_count=0`.
- Console: no browser `error`, `warn`, or `warning` log entries were captured for the path.
- Network contract: the restore path is `GET /api/v1/production-canvas/runs/{run_id}` from `production-canvas.endpoints.ts` to `production_canvas.py`; the route restored `Run ID 567b0cefc948467988f463e251e2b3b3` and showed `已恢复`. The in-app browser did not expose a network panel, and its restricted page evaluation scope did not expose `fetch` or `localStorage` for a token-authenticated GET retry.
- Evidence artifact: `artifacts/runs/2026-07-02T19-50-08Z-canvas-task-evidence-edge-hide/in-app-browser-result.json`.

3. Conflict signals and corrections:

- Initial browser issue: task evidence nodes still showed the generic `连线编辑` UI after the prior target-filtering fix.
- Reproduction: added a failing component test that rendered `ProductionCanvasEdgeControls` against a task evidence node and expected no `连线编辑`.
- Final verified state: selected task evidence nodes keep their task evidence surface but no longer show the generic edge editor.

## Next Steps

- Continue with the next small infinite-canvas workflow increment.
- `npm run build` was not run because this change is client-side component behavior only, not route, layout, auth, config, or hydration-sensitive code.
- No files were staged or committed; unrelated existing worktree changes were left untouched.

## Linked Commits

- Not committed in this turn.
