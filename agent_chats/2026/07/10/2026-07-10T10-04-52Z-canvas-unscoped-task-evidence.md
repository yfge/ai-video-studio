---
title: Canvas unscoped task evidence cleanup
date: 2026-07-10T10:04:52Z
area: ai-pic-frontend
---

## User Prompt

继续完善无限画布功能；用户指出当前整体链路仍然断，需要用 Docker dev 栈和内置浏览器验证。

## Goals

- Prevent historical task evidence without a `canvas_run_id` from being restored into a server-backed canvas run.
- Stop unscoped task nodes such as `Task #101/#102` from seeding `task_id` into unrelated skill nodes.
- Keep current run task evidence and current run metadata visible.

## Changes

- Treat saved task-context nodes with no `canvas_run_id` as unscoped when restoring a server run:
  - if the saved node id matches a current plan node, restore the plan node with the saved layout;
  - otherwise drop the unscoped task evidence node.
- Added a regression test proving an unscoped `summary-task-2` is dropped and a stale `skill-asset-select` falls back to current run plan outputs.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasServerRestore.test.ts` -> pass, 6 tests.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasPersistence.test.tsx` -> pass, 9 tests.
- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasPlanner.test.tsx` -> pass, 10 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/productionCanvasRunNodes.ts ai-pic-frontend/tests/productionCanvasServerRestore.test.ts` -> pass.

2. Browser or MCP validation:

- Environment and entry URL: `docker/dev_in_docker.sh`, `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Browser path: Codex In-app Browser loaded the target run while logged in as `geyunfei`, selected `Asset Selection`, and read the node detail output rows.
- Console: no warnings or errors.
- Result: UI still shows current run id `48d62cd56e1646c4b3f0c77c1a3cd4a6` and `Task #6266`; UI no longer shows stale run `0cae5687386f4697ae52d9eb6c3e6580`, `Task #6267`, `Task #101`, or `Task #102`. `Asset Selection` output rows are now only `canvas_run_id`, `canvas_task_id: 6266`, and `required_inputs: virtual_ip_id, environment_id`; `task_id: 102` is gone.

3. Conflict signals and corrections:

- Initial state after the prior slice still showed `task_id: 102` on `Asset Selection`.
- API inspection showed `summary-task-1/2` had task ids but no `canvas_run_id`, while `skill-asset-select` still stored stale `canvas_task_id/task_id: 6267`.
- Restore now rejects unscoped task-context nodes for server runs, so historical task summaries cannot contaminate ordinary skill execution inputs.

## Next Steps

- Fill `virtual_ip_id` and `environment_id`, then execute `Asset Selection` and the next ready skill to verify the forward execution chain beyond restore.
- Consider an explicit cleanup/save affordance for contaminated persisted `saved_state`; restore remains non-mutating.

## Linked Commits

Pending.
