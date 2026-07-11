## User Prompt

继续完善无限画布功能；先提交现有变更。

## Goals

- Add reusable domain templates without exposing provider implementation graphs.
- Insert every template as a persistent, executable, typed subflow with unique identities.
- Preserve active Run and production context across save and restoration.

## Changes

- Added role look, scene look, shot review, and delivery templates using existing canvas Skills and typed ports.
- Added a toolbar template picker and one-step insertion as an undoable graph definition change.
- Each insertion creates unique node, edge, and section identities, moves the viewport to the inserted group, and preserves group selection without opening a premature single-node inspector.
- Propagated script, episode, asset, task, and active canvas Run context into inserted subflows.
- Added one delayed retry for the transient candidate 404 that can occur before a new node is persisted; persistent and authorization errors are not retried.
- Moved the route shell out of the Board module to keep the changed production files within repository size contracts.
- Updated the design and task board to mark provider-agnostic templates complete while leaving scale work open.

## Validation

1. Local checks:

- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `cd ai-pic-frontend && npm run lint` -> 0 errors; 3 pre-existing warnings.
- Focused template, candidate loading, candidate review, and Board tests -> 20 passed during iteration.
- `cd ai-pic-frontend && npm run test` -> 322 passed.
- `cd ai-pic-frontend && npm run build` -> pass; `/canvas` generated successfully.

2. Browser validation:

- Entry URL: `http://localhost:8089/canvas?run_id=a435551897f44c88a640988b997ca9b8`.
- Owner selected the shot-review template, inserted reusable image and video candidate nodes with a typed `approved_image -> start_frame` edge, and saved the canvas.
- Save request `req-1783793960538-ff6kjsz4` returned 200; template candidate requests including `req-1783793961541-3s5lxac3` returned 200.
- Candidate review showed a valid empty state instead of an HTTP error when the selected script had no persisted candidate history.
- Refresh restored four template nodes and two persistent sections with no 404, 422, console error, or warning.
- Evidence: `artifacts/runs/canvas-template-20260712T021000Z/shot-review-restored.jpg`.

3. Conflict signals and corrections:

- A newly selected media template node initially queried candidates before autosave and returned 404. Candidate loading now retries one transient 404, while insertion keeps group selection until the user selects a node.
- Shared context initially propagated `task_id` but not `canvas_run_id`, so restoration safety removed template nodes as unscoped. Template nodes now inherit the active Run ID explicitly.
- Active task polling can delay debounced autosave. The browser path explicitly saved after insertion and verified the persisted restoration result.

## Next Steps

- Define measurable large-canvas interaction and rendering budgets.
- Add viewport virtualization and scale fixtures without hiding selected or executing nodes.
- Run the consolidated provider-backed image-to-video-to-Timeline release validation.

## Linked Commits

- `feat(canvas): add reusable domain subflows`
