---
id: 2026-07-11T15-31-22Z-canvas-candidate-history
date: 2026-07-11T15:31:22Z
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - canvas
  - candidate-review
  - recovery
  - media-assets
related_paths:
  - ai-pic-backend/app/repositories/production_canvas_candidate_repository.py
  - ai-pic-backend/app/services/production_canvas/candidate_history.py
  - ai-pic-backend/app/services/production_canvas/candidate_review.py
summary: Preserve canvas candidate history independently from mutable storyboard frames and restore legacy selected assets.
---

## User Prompt

按照完善后的设计完成无限画布功能，保证原子化提交。

## Goals

- Close the known candidate-list restoration gap on saved canvas runs.
- Preserve candidate history across storyboard replacement and generation retries.
- Keep candidate reads from changing graph lifecycle or stale state.

## Changes

- Added a focused candidate asset repository with user-scoped media lookup and history enumeration.
- Persisted Run ID, node ID, frame, clip, prompt, model, and duration references in existing `MediaAsset` metadata.
- Merged persisted asset history, current storyboard candidates, Timeline candidates, and the legacy selected asset when listing a review node.
- Kept candidate history out of canvas saved state so a read cannot trigger stale propagation or be overwritten by browser autosave.
- Added an integration regression that replaces storyboard media after approval and still restores both historical candidates and the selected state.

## Validation

- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_candidate_history_api.py tests/integration/test_production_canvas_candidate_review_api.py` - passed: 3 tests.
- `ruff check <changed Python paths>` and `black <changed Python paths>` - passed.
- `python scripts/check_repo_contracts.py --mode diff <changed paths>` - passed.
- `cd ai-pic-backend && python run_tests.py quick` - blocked before tests by the existing Python 3.13 dependency resolution conflict: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires Pydantic 2.7.4 or newer on this interpreter.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` - passed; backend and frontend images were built locally without push using tag `94769d18`.
- In-app browser at `http://localhost:8089/canvas?run_id=aa6e7886ed874556bcfd8490eaecfb8e` - restored the previously empty Image Candidates review. The page showed media previews and one `已选用` candidate; `暂无可评审候选` was absent.
- Decisive backend requests: candidate GET request IDs `req-1783783815150-yj8lykcb` and `req-1783783815177-wwks1oa6` both returned 200. The expired-session 401 immediately before login was reproduced and corrected through the normal login flow.
- Persistence assertion after browser restore: image node remained `approved`, selected asset remained `380`, no candidate history was written to node outputs, and 21 asset references were associated with the Run and node.
- Screenshot: `artifacts/runs/canvas-candidate-history-20260711T153000Z/restored-candidates.jpg`.

## Next Steps

- Implement explicit candidate rejection and rejection reason transitions.
- Repeat the approve, switch, stale, reject, and Run ID restore path in one controlled browser run.
- Update the production canvas design and task board after the review workflow is complete.

## Linked Commits

- Pending commit created from this ledger entry.
