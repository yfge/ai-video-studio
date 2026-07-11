---
id: 2026-07-11T10-50-43Z-canvas-stale-runtime
date: "2026-07-11T10:50:43Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - backend
  - stale-propagation
  - typed-graph
related_paths:
  - ai-pic-backend/app/schemas/production_canvas.py
  - ai-pic-backend/app/services/production_canvas/execution_persistence.py
  - ai-pic-backend/app/services/production_canvas/executor.py
  - ai-pic-backend/app/services/production_canvas/graph_runtime.py
  - ai-pic-backend/app/services/production_canvas/run_persistence.py
  - ai-pic-backend/app/services/production_canvas/stale_runtime.py
  - ai-pic-backend/tests/integration/test_production_canvas_downstream_api.py
  - ai-pic-backend/tests/unit/test_production_canvas_stale_runtime.py
summary: Persisted graph input fingerprints, propagated stale state across descendants, and prevented stale outputs from satisfying downstream ports.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交

## Goals

- Detect when an executed node no longer consumes the same definition, binding, or upstream value.
- Mark the changed node and affected descendants stale without invalidating unrelated nodes.
- Prevent stale source outputs from silently satisfying downstream required ports.
- Allow explicit Run Node or Run Downstream to refresh stale work.

## Changes

- Added a persisted execution input fingerprint to graph v2 nodes and node execution evidence.
- Fingerprinted node definition version, incoming typed bindings, and resolved upstream values after each attempted execution.
- Compared the current graph with the last consumed fingerprint during Run saves and propagated stale state through executable descendants.
- Preserved stale status during graph evaluation instead of incorrectly promoting it back to Ready.
- Excluded stale source outputs from typed input resolution, making dependent required ports visibly missing until rerun.
- Persisted refreshed fingerprints with execution results so rerunning a stale subgraph returns completed nodes to their actual runtime status.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_production_canvas_stale_runtime.py tests/integration/test_production_canvas_downstream_api.py tests/integration/test_production_canvas_graph_api.py tests/unit/test_production_canvas_graph_runtime.py tests/unit/test_production_canvas_executor.py tests/unit/test_production_canvas_run_persistence.py -q` -> 12 passed, 30 warnings.
- `cd ai-pic-backend && pytest` -> 2442 passed, 88 skipped, 3135 warnings in 122.47s.
- Integration proof: a root typed-output change preserved root Ready, marked middle and leaf Stale, made the stale middle output unavailable to leaf, then Run Downstream from middle consumed the new value and restored both nodes to Ready.
- Unit proof: increasing root `definition_version` marked root and every descendant Stale; an unchanged graph produced no false stale state.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` -> passed; all service and test files remain below repository limits.
- `git diff --check` -> passed.
- Scoped pre-commit hooks -> passed, including ruff, black, isort, repository contracts, ledger enforcement, and the backend quick gate.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push.

## Next Steps

- Apply the server-returned saved state after frontend saves so stale impact appears immediately.
- Preserve server-owned execution fingerprints through frontend restore and autosave.
- Add candidate approval changes as first-class selected-output mutations that trigger this stale contract.

## Linked Commits

- `86ee2823 feat(canvas): expose downstream execution controls`
- Pending.
