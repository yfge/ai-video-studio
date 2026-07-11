---
id: 2026-07-11T15-06-25Z-canvas-stale-impact
date: 2026-07-11T15:06:25Z
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - candidate-review
  - persistence
  - stale-state
related_paths:
  - ai-pic-backend/app/services/production_canvas
  - ai-pic-frontend/src/components/features/canvas
summary: Protect candidate review runtime state and preview downstream stale impact before switching an approved asset.
---

## User Prompt

继续完善无限画布功能；整体链路仍然断开；先提交现有变更。

## Goals

- Preview which executed downstream nodes will become stale before switching an approved candidate.
- Prevent browser autosave and terminal task evidence from overwriting authoritative review state.
- Ensure automatic execution after whole-canvas creation uses the newly planned run id.
- Commit the current repair as one traceable canvas state-consistency change.

## Changes

- Added authoritative stale-impact data to candidate review responses and an inline confirmation step for candidate switching.
- Merged browser-owned canvas configuration with server-owned runtime, approval, and selection state on save.
- Preserved `stale` and `approved` node statuses while reconciling completed or cancelled task evidence.
- Routed automatic ready-node execution through the run id returned by the new plan instead of a previously active run.
- Split the candidate item UI to keep canvas frontend files within repository size limits and added focused regression coverage.

## Validation

- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_candidate_review_api.py tests/unit/test_production_canvas_stale_runtime.py tests/unit/test_production_canvas_run_persistence.py tests/unit/test_production_canvas_client_state_merge.py` - passed: 7 tests.
- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_graph_api.py tests/integration/test_production_canvas_run_control_api.py tests/integration/test_production_canvas_candidate_review_api.py tests/unit/test_production_canvas_stale_runtime.py tests/unit/test_production_canvas_run_persistence.py tests/unit/test_production_canvas_client_state_merge.py` - passed: 15 tests after narrowing stale-client protection so current-fingerprint updates remain valid.
- `cd ai-pic-backend && pytest -q` - passed: 2457 tests, 88 skipped. The first full run exposed three canvas state-merge regressions; all three were reproduced directly, fixed, and passed in the final full rerun.
- `cd ai-pic-frontend && npm run test -- --run tests/productionCanvasCandidateReview.test.tsx tests/productionCanvasExecutionTracking.test.ts tests/productionCanvasPersistenceSync.test.ts tests/productionCanvasPlanner.test.tsx` - the repository script ran the full frontend suite; passed: 311 tests.
- `cd ai-pic-frontend && npm run lint` - passed with 3 pre-existing warnings and no errors.
- `cd ai-pic-frontend && npm run build` - passed, including the `/canvas` production route.
- `python scripts/check_repo_contracts.py --mode diff <changed paths>` - passed.
- `python scripts/check_repo_docs.py && python scripts/check_repo_contracts.py --mode audit` - passed.
- `pre-commit run --all-files` - failed on the repository baseline: 69 existing ruff findings; all-files formatters also rewrote unrelated historical files. Those mechanical rewrites were reverted before delivery, and no unrelated path is included in this commit.
- `pre-commit run --files <changed paths>` - passed all configured hooks, including formatting, repository checks, backend quick tests, and frontend lint.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` - passed; backend and frontend images were built locally without push using tag `7fbacecd`. The classic builder ignored the platform override as reported by the script.
- In-app browser at `http://localhost:8089/canvas` - created controlled canvas runs, observed the candidate-switch warning list `Video Candidates`, and verified a newly planned run id was used by automatic execution. Browser and backend evidence contradicted the initial autosave and task-reconciliation assumptions, which led to the client-state merge, status-preservation, and run-id fixes in this commit.
- Browser residual: on the final isolated run `aa6e7886ed874556bcfd8490eaecfb8e`, restored approved nodes were visible, but candidate review later returned an empty candidate list after cancellation and deterministic state seeding. This commit does not claim the complete canvas production chain is closed.

## Next Steps

- Diagnose the final candidate-list restoration gap and repeat the approve, stale, autosave, and restore browser path end to end.
- Continue the remaining rejection/comment workflow and align the infinite-canvas design document with verified behavior.

## Linked Commits

- Pending commit created from this ledger entry.
