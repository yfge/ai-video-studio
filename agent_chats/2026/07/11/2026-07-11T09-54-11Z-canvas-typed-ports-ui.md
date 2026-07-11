---
id: 2026-07-11T09-54-11Z-canvas-typed-ports-ui
date: "2026-07-11T09:54:11Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - frontend
  - typed-graph
  - browser-evidence
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasModel.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPorts.ts
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasEdgeControls.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPersistence.ts
  - ai-pic-frontend/tests/productionCanvasPorts.test.ts
summary: Adopted graph v2 in the production canvas UI with visible versioned ports, compatible typed bindings, and legacy v1 restore compatibility.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交

## Goals

- Make the frontend consume the graph v2 contract from `b09f794e`.
- Replace arbitrary visual edge creation with type-compatible port binding.
- Persist new canvas definitions as v2 without breaking legacy untyped Run IDs.
- Prove the visible and persisted behavior in the running `dev_in_docker` stack and in-app browser.

## Changes

- Added the full node lifecycle vocabulary, versioned node ports, typed edge metadata, selected-output bindings, and ordered multi-input fields to frontend/API types.
- Defined domain port contracts for static production nodes and dynamic canvas skills.
- Rendered input/output port handles on node cards and solid typed edges on the canvas.
- Replaced arbitrary target selection with compatible source-port to target-port discovery; notes and task evidence are no longer executable edge targets.
- Saved complete definitions as `graph_version=2`, serialized node ports and typed edges, and retained graph v1 for legacy untyped edges.
- Updated execution affordances so restored `pipeline` skill nodes remain runnable.

## Validation

- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings and no errors.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvas*.test.tsx tests/productionCanvas*.test.ts` -> 157 passed.
- `cd ai-pic-frontend && npm run build` -> passed; `/canvas` generated successfully.
- `python scripts/check_repo_contracts.py --mode diff ...` -> passed; `ProductionCanvasBoard.tsx` remains at the 250-line hard limit.
- Scoped pre-commit hooks -> passed after applying the repository Prettier version, including frontend lint, contracts, docs, and ledger enforcement.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> backend and frontend images built locally without push; npm audit reported the existing 1 moderate and 1 high dependency findings.
- Environment: running `dev_in_docker` stack at `http://localhost:8089/canvas`, backend health 200 at `http://localhost:8000/health`.
- In-app browser path: login -> reset stale local layout -> select Image Candidates -> remove `approved_image -> start_frame` -> verify it is the only compatible option -> recreate the selected-output binding -> create and autosave Run `d2205708bad847a39edbabf84c0bce60`.
- Browser DOM: Brief has zero input ports and one output port after reset; seven default edges are typed; image/video port titles expose `image` compatibility; rebuilt edge reports `selected_output`.
- Browser console: no warning or error entries during the validation path.
- Persisted DB evidence: Task `6289` saved `graph_version=2`; all seven edges include `edge_id`, `from_port`, `to_port`, and `binding_type`; `image-approved_image-to-video-start_frame` persisted as `selected_output`.
- Screenshot: `artifacts/runs/canvas-typed-graph-20260711T094500Z/typed-ports.png`.

## Next Steps

- Add direct port drag-to-connect behavior on the same typed edge contract.
- Resolve approved upstream port values into real execution request context, graph readiness, and downstream scope.

## Linked Commits

- `b09f794e feat(canvas): validate typed graph definitions`
- Pending.
