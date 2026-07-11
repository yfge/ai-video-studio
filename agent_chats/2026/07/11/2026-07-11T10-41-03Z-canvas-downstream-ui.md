---
id: 2026-07-11T10-41-03Z-canvas-downstream-ui
date: "2026-07-11T10:41:03Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - frontend
  - run-downstream
  - browser-evidence
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasExecutionResults.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasNodeExecution.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - ai-pic-frontend/tests/productionCanvasDownstream.test.tsx
  - tasks.md
summary: Connected the canvas UI to node-scoped graph execution, added Run Downstream controls, and published every server execution to its matching node.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交

## Goals

- Send explicit node identity and execution scope to the graph runtime.
- Prevent execution from racing ahead of the current unsaved graph definition.
- Expose distinct Run Node and Run Downstream operator commands.
- Publish every downstream execution result to the correct canvas node and tracker.

## Changes

- Added frontend API types for node-scoped requests, resolved inputs, execution order, and per-node downstream executions.
- Saved the current canvas before graph-backed execution and aborted dispatch when that save fails.
- Sent `node_id` and `execution_scope` for every manual execution.
- Mapped each server execution back to its matching source node, including independent task/render evidence tracking.
- Added separate `运行节点` and `运行下游` controls with scope-specific busy states in the node inspector.
- Preserved canvas keyboard focus after either inspector or node-card execution.
- Updated the task board to mark typed graph and real Run Downstream work complete while leaving stale propagation and candidate review open.

## Validation

- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings and no errors.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvas*.test.tsx tests/productionCanvas*.test.ts` -> 158 passed.
- `cd ai-pic-frontend && npm run build` -> passed; `/canvas` generated successfully.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` -> passed; Board and planner remain below the 250-line limit.
- In-app browser environment: `dev_in_docker` at `http://localhost:8089/canvas?run_id=d2205708bad847a39edbabf84c0bce60`.
- Browser path: restore Run -> select Brief Skill -> add typed `production_brief -> Asset Selection.production_brief` edge -> click `运行下游`.
- Visible result: current graph saved before execution; Brief Skill remained Ready; Asset Selection executed with the upstream brief, became Blocked, and displayed `required_inputs: virtual_ip_id, environment_id`; no media task was dispatched.
- Browser console: no warning or error entries.
- Persisted DB evidence: Task `6289` retained `graph_version=2`; edge `skill-brief-compose-production_brief-to-skill-asset-select-production_brief` persisted as a value binding; `skill-asset-select` persisted as Blocked with the two required inputs.
- Screenshot: `artifacts/runs/canvas-downstream-20260711T102900Z/run-downstream.png`.
- Scoped pre-commit hooks -> passed, including Prettier, repository contracts, ledger enforcement, and frontend lint.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push; npm reported the existing 1 moderate and 1 high dependency findings.

## Next Steps

- Propagate stale state to descendants when node definitions, bindings, or selected outputs change.
- Add persistent media candidate history and explicit image/video approval transitions.
- Complete the approved image to video to stable Timeline clip vertical slice.

## Linked Commits

- `25ecb4e1 feat(canvas): execute typed downstream graph`
- Pending.
