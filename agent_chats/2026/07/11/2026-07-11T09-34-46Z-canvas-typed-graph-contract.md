---
id: 2026-07-11T09-34-46Z-canvas-typed-graph-contract
date: "2026-07-11T09:34:46Z"
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
related_paths:
  - ai-pic-backend/app/schemas/production_canvas.py
  - ai-pic-backend/app/services/production_canvas/graph_validation.py
  - ai-pic-backend/tests/unit/test_production_canvas_graph_validation.py
  - ai-pic-backend/tests/integration/test_production_canvas_graph_api.py
summary: Added the backward-compatible v2 typed graph persistence contract and strict backend DAG validation for production canvas runs.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交

## Goals

- Start Phase 1 of `docs/design/production-canvas.md` with an authoritative backend graph contract.
- Preserve existing `graph_version=1` Run ID state while making new v2 definitions executable only after strict validation.
- Keep this backend contract independently testable and reversible before frontend adoption.

## Changes

- Added the full canvas lifecycle status vocabulary, typed input/output ports, node definition versions, typed edge bindings, required flags, and stable multi-input ordering.
- Added `graph_version=2` while retaining version 1 defaults for existing saved runs.
- Added backend validation for duplicate node/port/edge identities, duplicate bindings, unknown nodes or ports, self-edges, cycles, incompatible types, single-input fan-in, unordered multi-input bindings, and executable note/task-evidence connections.
- Added unit coverage for graph invariants and API coverage proving typed state save, restore, and 422 rejection before persistence.

## Validation

- `cd ai-pic-backend && python -m black ... && python -m ruff check ...` -> passed for all changed Python files.
- `cd ai-pic-backend && pytest tests/unit/test_production_canvas_graph_validation.py tests/unit/test_production_canvas_run_persistence.py tests/integration/test_production_canvas_graph_api.py -q` -> 17 passed.
- `cd ai-pic-backend && pytest` -> 2436 passed, 88 skipped, 3135 warnings in 129.75 seconds.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed; all changed files remain within repository size limits.
- Scoped pre-commit hooks -> passed, including backend quick gate, formatting, repository contracts, docs, and ledger enforcement.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push.

## Next Steps

- Add v2 port definitions and typed edge editing/persistence to the frontend while restoring legacy v1 runs compatibly.
- Route approved upstream values through typed bindings into readiness and execution planning.

## Linked Commits

- Pending.
