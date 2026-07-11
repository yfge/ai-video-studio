---
id: 2026-07-11T15-50-40Z-canvas-candidate-rejection
date: 2026-07-11T15:50:40Z
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - candidate-review
  - rejection
  - stale-propagation
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/production_canvas.py
  - ai-pic-backend/app/services/production_canvas/candidate_rejection.py
  - ai-pic-backend/app/services/production_canvas/candidate_review_state.py
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasCandidateItem.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasCandidateReview.tsx
summary: Add persistent candidate rejection decisions and restore the review workflow across saved canvas runs.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- Add explicit media candidate rejection with an optional reason.
- Persist candidate review decisions independently from mutable canvas node state.
- Return a rejected selected node to review and mark dependent nodes stale.
- Preserve rejection and recovery behavior after restoring a saved Run ID.

## Changes

- Added a user-scoped candidate rejection endpoint and review-state response schema.
- Persisted pending, approved, and rejected decisions with reviewer, timestamp, and rejection reason in the candidate asset reference.
- Cleared selected output when its candidate is rejected, incremented the node definition version, and propagated stale state to downstream nodes.
- Updated approval to clear a prior rejection and record the new approved decision.
- Added candidate review controls for reject, optional reason entry, cancellation, confirmation, rejected-state display, and re-selection.
- Added backend integration coverage and frontend interaction coverage for rejection, stale propagation, recovery, and API failures.

## Validation

- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_candidate_rejection_api.py tests/integration/test_production_canvas_candidate_history_api.py tests/integration/test_production_canvas_candidate_review_api.py tests/unit/test_production_canvas_stale_runtime.py` - passed: 6 tests.
- `cd ai-pic-backend && pytest -q` - passed: 2459 tests, 88 skipped.
- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasCandidateReview.test.tsx` - passed: 1 test.
- `cd ai-pic-frontend && npm run test` - passed: 311 tests.
- `cd ai-pic-frontend && npm run lint` - passed with 3 pre-existing warnings and no errors.
- `cd ai-pic-frontend && npm run build` - passed; the `/canvas` route was included.
- `python scripts/check_repo_docs.py` and `python scripts/check_repo_contracts.py --mode audit` - passed.
- `pre-commit run --files <candidate rejection slice>` - passed after `isort` and `prettier` normalized the changed files; backend quick gate, frontend lint, repository contracts, and ledger enforcement all passed.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` - passed; backend and frontend images were built locally without push using tag `264678c4`. The build retained the existing Next.js workspace-root warning and reported two frontend dependency audit findings (one moderate and one high).
- In-app browser path: `http://localhost:8089/canvas?run_id=aa6e7886ed874556bcfd8490eaecfb8e`. Rejected selected asset `380` with reason `浏览器回归：角色连续性不符合`, restored the Run ID, confirmed the reason persisted and no candidate remained selected, re-selected the rejected candidate, then switched to asset `398` after the downstream-impact confirmation.
- Decisive requests: rejection `req-1783784752392-76ndtvdd`, re-approval `req-1783784866967-65w2coee`, and candidate switch `req-1783784915138-5sfjooxb` all returned 200.
- Final persistence assertion: `skill-image-candidates` was `approved` at definition version 6 with approved asset `398`; `skill-video-candidates` was `stale`. Candidate asset references retained reviewer and review timestamps.
- Screenshots: `artifacts/runs/canvas-candidate-rejection-20260711T154500Z/rejected.jpg` and `artifacts/runs/canvas-candidate-rejection-20260711T154500Z/switched.jpg`.
- The in-app Browser surface exposed the visible final state and backend request IDs; it did not expose a separate console-errors API in this session. No visible Next.js alert was present after the workflow.

## Next Steps

- Align the production canvas design document and canonical task board with the implemented Phase 1-3 workflow.
- Audit remaining Phase 4 collaboration and performance work separately from this review slice.

## Linked Commits

- Pending commit created from this ledger entry.
