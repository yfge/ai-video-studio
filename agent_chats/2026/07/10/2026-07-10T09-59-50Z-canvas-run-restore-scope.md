---
title: Canvas run restore scope
date: 2026-07-10T09:59:50Z
area: ai-pic-frontend
---

## User Prompt

继续完善无限画布功能；用户指出 `/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6` 整体链路仍然断，可以拉起 `dev_in_docker` 并用内置浏览器验证。

## Goals

- Restore a canvas run without letting saved nodes from another run leak into the visible canvas state.
- Keep the canvas run task id as `canvas_task_id` metadata instead of satisfying ordinary skill `task_id` inputs.
- Preserve valid downstream task evidence propagation for real executed tasks.

## Changes

- Added run-scoped node restoration in `productionCanvasRunNodes.ts`:
  - saved nodes carrying a different `canvas_run_id` are replaced with the current run plan node when possible, preserving saved layout;
  - stale non-plan task evidence from another run is dropped;
  - skill nodes are re-stamped with the current `canvas_run_id` / `canvas_task_id`, and stale `task_id` / `dispatched_task_id` values equal to the previous canvas task are removed.
- Added `productionCanvasTaskContext.ts` so `applyProductionCanvasContext` does not treat the canvas run's own `canvas_task_id` as an ordinary task input.
- Added server-restore regression coverage for current-run task evidence, cross-run saved task evidence, and run plan nodes that require `task_id`.
- Split restoration helpers out of `productionCanvasPersistence.ts` to keep touched files under the repository file-size contract.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasServerRestore.test.ts` -> pass, 5 tests.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasPersistence.test.tsx` -> pass, 9 tests.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasPlanner.test.tsx` -> pass, 10 tests; confirmed Task #77 / Task #88 still route to downstream skills.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasSkillPlannerRunId.test.tsx` -> pass, 1 test.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasGraph.test.tsx` -> pass, 19 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts ai-pic-frontend/src/components/features/canvas/productionCanvasPersistence.ts ai-pic-frontend/src/components/features/canvas/productionCanvasRunNodes.ts ai-pic-frontend/src/components/features/canvas/productionCanvasTaskContext.ts ai-pic-frontend/tests/productionCanvasServerRestore.test.ts` -> pass.

2. Browser or MCP validation:

- Environment and entry URL: `docker/dev_in_docker.sh`, `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Browser path: Chrome DevTools MCP returned `HTTP Not Found` on `127.0.0.1:9222/json/version`, so validation used the Node browser client against Codex In-app Browser. The page was logged in as `geyunfei`, loaded the target run, and showed `已恢复`.
- Console: no warning or error logs from the validated tab.
- Network/API: authenticated API read for the same run returned `success: true`, `task_id: 6266`, `saved_node_count: 14`; the server `saved_state` still contains `0cae5687386f4697ae52d9eb6c3e6580`, `Task #6267`, and `Task #6266`, proving the browser check exercised contaminated persisted data.
- Result: restored UI contains current run id `48d62cd56e1646c4b3f0c77c1a3cd4a6`, does not contain stale run `0cae5687386f4697ae52d9eb6c3e6580`, and does not contain `Task #6267`. Selected `Asset Selection` shows `canvas_task_id: 6266`, `required_inputs: virtual_ip_id, environment_id`, and still shows `task_id: 102` from existing task evidence.

3. Conflict signals and corrections:

- Initial assumption: removing the `canvas_task_id -> task_id` fallback was sufficient.
- Contradicting evidence: the browser still showed current run task evidence affecting skill outputs.
- Reproduction and fix: added task context filtering so a node with `task_id === canvas_task_id` does not become the shared skill `task_id`; added regression coverage for this case.
- Final verified state: cross-run contamination and `Task #6267` no longer render from the target run; the remaining `task_id: 102` is a separate task-evidence propagation issue for the next slice.

## Next Steps

- Decide whether task evidence like `Task #101/#102` should be scoped to only skills that require `task_id`, instead of being merged into every skill node.
- Consider a one-time cleanup or explicit save path for contaminated historical `saved_state`; this change intentionally fixes restore-time isolation without mutating server state on read.

## Linked Commits

Pending.
