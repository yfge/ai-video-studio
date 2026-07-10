---
id: 2026-07-10T11-18-58Z-canvas-reference-artifact-frontend
date: "2026-07-10T11:18:58Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - artifacts
  - image-candidates
related_paths:
  - ai-pic-frontend/src/utils/api/types/production-canvas.types.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasSkillNodes.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasSharedContext.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasState.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - ai-pic-frontend/tests/productionCanvasState.test.ts
  - ai-pic-frontend/tests/productionCanvasSkillPlannerRunId.test.tsx
  - ai-pic-frontend/tests/productionCanvasServerRestore.test.ts
summary: Propagate completed canvas asset references into Image Candidates and verify the real storyboard worker handoff.
---

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- Make completed role/environment image artifacts available to downstream `Image Candidates`.
- Avoid propagating stale task evidence or artifacts from running/failed retries.
- Prove the handoff through the real browser, task record, worker, persisted storyboard output, and page restore.

## Changes

- Added string-array execution request support and routed `reference_artifacts` from canvas node outputs.
- Extracted shared canvas context derivation into a focused module to stay within repository file-size contracts.
- Collected only supported artifact refs from completed source skill nodes; task evidence notes are ignored and stale refs are cleared while a source retries.
- Reapplied the artifact context during live node updates and server-backed run restore.
- Added focused context, request-routing, and restore regression coverage.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasState.test.ts tests/productionCanvasSkillPlannerRunId.test.tsx tests/productionCanvasServerRestore.test.ts tests/productionCanvasExecutionTracker.test.tsx tests/productionCanvasExecutionTracking.test.ts tests/productionCanvasPlanner.test.tsx tests/productionCanvasMediaControls.test.tsx tests/productionCanvasPersistence.test.tsx` -> pass, 37 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ...` -> pass after extracting `productionCanvasSharedContext.ts`.
- `git diff --check` -> pass.
- Scoped `pre-commit run --files ...` -> pass, including Prettier, contracts, ledger enforcement, and frontend lint.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> pass; backend and frontend production images built locally without push.

2. Browser and runtime validation:

- Run URL: `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6` in the Codex in-app browser.
- Restored `environment_images:13:1` from completed source `Task #6270`; selecting `Image Candidates` showed the same artifact in its execution outputs.
- Entered existing storyboard script `130`, limited media indexes to `[0]`, selected `gpt-image-2`, and executed `Image Candidates`.
- The POST request carried `reference_artifacts: ["environment_images:13:1"]`; backend `Task #6271` stored the resolved environment OSS URL in `parameters.reference_images`, targeted the same canvas run, and dispatched the existing `STORYBOARD_IMAGE_GENERATION` worker.
- Worker completed `Task #6271` after 233.23 seconds. Script `130` frame `0` persisted four new start-image candidates dated `20260710`, with the generated environment URL in `reference_images`.
- The source node and task evidence changed to completed/review, and `Video Candidates` became ready from the propagated `script_id: 130`.
- Full reload retained `Task #6271`, the artifact ref, script context, `Image Candidates` review state, and `Video Candidates` ready state. Browser console contained no warnings or errors.
- Screenshots: `artifacts/runs/canvas-reference-chain-20260710T111600Z/image-candidates-completed.png` and `artifacts/runs/canvas-reference-chain-20260710T111600Z/image-candidates-restored.png`.

3. Residual signal:

- The second OpenAI call for the end-frame candidates logged `图像生成失败: openai 错误:`. The frame retained its existing end image and the task completed after new start candidates were persisted. Partial candidate-generation semantics remain a separate worker-level follow-up.

## Next Steps

- Make storyboard candidate tasks report partial provider failures explicitly instead of relying only on the final task status.
- Continue the canvas chain through `Video Candidates`, then verify Timeline and report evidence propagation.

## Linked Commits

Pending.
