---
id: 2026-07-11T10-07-55Z-canvas-graph-runtime
date: "2026-07-11T10:07:55Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - backend
  - typed-graph
  - execution-runtime
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/production_canvas.py
  - ai-pic-backend/app/schemas/production_canvas.py
  - ai-pic-backend/app/services/production_canvas/executor.py
  - ai-pic-backend/app/services/production_canvas/graph_runtime.py
  - ai-pic-backend/app/services/production_canvas/pipeline_execution.py
  - ai-pic-backend/app/services/production_canvas/run_persistence.py
  - ai-pic-backend/tests/integration/test_production_canvas_graph_api.py
  - ai-pic-backend/tests/unit/test_production_canvas_graph_runtime.py
summary: Resolved production canvas execution inputs from saved typed graph bindings and exposed server-side graph readiness and topology.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交

## Goals

- Make typed graph bindings affect execution instead of remaining presentation-only metadata.
- Block dispatch when a selected node is missing required upstream inputs.
- Expose server-evaluated node readiness and deterministic downstream topology.
- Preserve the existing execution dispatchers and legacy graph behavior.

## Changes

- Added graph-aware execution request and response fields for node identity, execution scope, resolved inputs, and execution order.
- Added a graph runtime that resolves incoming typed bindings from persisted graph v2 definitions, maps compatible source outputs into existing dispatcher requests, detects missing required ports, and computes topological/downstream order.
- Added `GET /api/v1/production-canvas/runs/{run_id}/graph` for server-evaluated node states and graph topology.
- Updated single-node execution to reject unknown graph nodes and missing required graph inputs before any dispatcher runs.
- Preserved review/approved lifecycle states while deriving draft/ready states for ordinary nodes.
- Extracted existing script, storyboard, and timeline dispatch helpers into `pipeline_execution.py` to keep backend service files within repository size limits.
- Added integration coverage proving an upstream production brief overrides the client prompt and that removing its source output blocks execution.

## Validation

- `cd ai-pic-backend && pytest tests/integration/test_production_canvas_graph_api.py tests/integration/test_production_canvas_api.py tests/unit/test_production_canvas_graph_validation.py tests/unit/test_production_canvas_graph_runtime.py tests/unit/test_production_canvas_executor.py -q` -> 24 passed, 44 warnings.
- `cd ai-pic-backend && pytest` -> 2438 passed, 88 skipped, 3135 warnings in 114.35s.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` -> passed.
- `git diff --check` -> passed.
- Scoped pre-commit hooks -> passed, including ruff, black, isort, repository contracts, ledger enforcement, and the backend quick gate.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push.

## Next Steps

- Send explicit `node_id` from the frontend and render server-evaluated node readiness.
- Implement actual ordered downstream dispatch; this commit returns the downstream execution order but does not run the sequence.
- Propagate stale state when bindings or selected upstream outputs change.

## Linked Commits

- `b09f794e feat(canvas): validate typed graph definitions`
- `d112398d feat(canvas): add typed port bindings`
- Pending.
