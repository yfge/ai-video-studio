---
id: 2026-07-11T16-28-41Z-canvas-candidate-branching
date: 2026-07-11T16:28:41Z
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - candidate-review
  - branching
  - lineage
related_paths:
  - ai-pic-backend/app/services/production_canvas/candidate_branching.py
  - ai-pic-backend/app/services/production_canvas/candidate_branch_context.py
  - ai-pic-backend/app/services/storyboard/candidate_lineage.py
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasCandidateBranchControls.tsx
  - docs/design/production-canvas.md
  - tasks.md
summary: Regenerate image and video candidates from an existing candidate while preserving parent lineage through the real media workers.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- Complete the candidate regenerate and branch interaction required by the production canvas design.
- Reuse the existing image and video workers instead of creating a parallel generation path.
- Preserve parent candidate, branch task, instruction, and generated child lineage across Run ID restoration.
- Keep the currently approved candidate selected while a branch generates.

## Changes

- Added a candidate branch endpoint that validates the candidate against the current Run and review node, then dispatches the existing media skill with the parent candidate context.
- Allowed a validated branch candidate to satisfy creative context while retaining strict missing-input blocking for ordinary graph execution.
- Scoped image and video branches to the parent candidate frame and preserved branch context through task payloads and media workers.
- Persisted generated URL lineage into storyboard frames and then into scoped `MediaAsset.canvas_candidate_refs` entries.
- Added candidate-card branch controls, optional variation instructions, submission feedback, and visible parent candidate and Task lineage.
- Kept candidate loading keyed to stable Run/node identity so a server state update no longer clears branch feedback or triggers a redundant reload.
- Refactored image queue input helpers below the service size limit and moved video storyboard writes behind `ScriptRepository`.
- Updated the production canvas design and canonical task board to mark candidate branching complete.

## Validation

- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_candidate_branch_api.py tests/integration/test_production_canvas_downstream_api.py tests/unit/test_production_canvas_graph_runtime.py tests/unit/test_canvas_candidate_lineage.py` - passed: 9 tests covering image/video dispatch, missing-input branch context, ordinary downstream behavior, and worker lineage.
- `cd ai-pic-backend && pytest -q` - passed: 2463 tests, 88 skipped.
- `cd ai-pic-frontend && npm run test` - passed: 311 tests.
- Frontend `npm run lint` - passed with 3 pre-existing warnings and no errors.
- Frontend `npm run build` - passed; `/canvas` was included.
- `python scripts/check_repo_docs.py` and `python scripts/check_repo_contracts.py --mode audit` - passed after the design and task-board sync.
- `pre-commit run --files <candidate branching slice>` - passed after Black and Prettier normalized the changed files; backend quick gate, frontend lint, repository contracts, and ledger enforcement were clean.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` - passed with a temporary empty `DOCKER_CONFIG`; backend and frontend images were built locally without push using tag `d3ab9f1d`.
- In-app browser Run `aa6e7886ed874556bcfd8490eaecfb8e`: parent candidate `398` remained selected while branch Task `6304` generated frame `16`. Request `req-1783787130047-8tqojbv6` returned 200.
- Worker result: Task `6304` completed and produced MediaAsset `441`; the candidate card showed `分支自候选 #398 · Task #6304 · 浏览器回归分支二：保留构图，将主光调整为冷蓝月光` before and after Run ID restore.
- Screenshots: `artifacts/runs/canvas-candidate-branch-20260712T002300Z/branch-submitted.jpg` and `artifacts/runs/canvas-candidate-branch-20260712T002300Z/branch-lineage.jpg`.
- Conflict signal: the first browser request returned 200 but produced no Task because ordinary graph missing-input checks blocked the branch. After allowing only validated branch context through that gate, a second request created Task `6303`. Its old worker process generated media without lineage; restarting `ai-video-celery-worker` loaded the changed worker code, and Task `6304` proved the complete lineage path.
- Build conflict signal: the first production build attempt hung in `docker-credential-desktop list` and was interrupted after approximately ten minutes. Re-running the local no-push build with a temporary empty Docker config bypassed the credential helper and completed successfully.

## Next Steps

- Implement canvas comments, role enforcement, and activity history as the next Phase 4 slice.
- Run the consolidated provider-backed image-to-video-to-Timeline release regression after the remaining Phase 4 work.

## Linked Commits

- Pending commit created from this ledger entry.
