---
id: 2026-07-16T12-05-54Z-canvas-dynamic-generation-nodes
date: "2026-07-16T12:05:54Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - progressive-reveal
  - task-progress
  - browser-validation
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasWorkspace.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasNodePreview.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasProgressiveReveal.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasProgressiveReveal.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasTaskExecutionTracker.ts
  - ai-pic-frontend/src/hooks/useGenerationTaskTracker.ts
  - ai-pic-frontend/tests/productionCanvasProgressiveReveal.test.ts
summary: Reveal planned Canvas nodes as execution advances and render live task content directly inside running node cards.
---

## User Prompt

这些结点应该是动态生成的吧？同时在生成过程中要可以直观显示内容。

## Goals

- Keep the backend-planned graph as the persisted source of truth while avoiding
  painting the whole future workflow before execution reaches it.
- Reveal executing nodes, task evidence, and settled downstream nodes in execution
  order.
- Show persisted task progress, readable content, percentages, and available media
  directly inside running node cards.
- Preserve existing Canvas editing, restore, filtering, task evidence, and
  single-video behavior.

## Changes

- Added a progressive-reveal state layer that starts with graph roots and their
  immediate executable context, reveals task evidence as soon as it is dispatched,
  and reveals downstream nodes only after the upstream task settles.
- Kept all planned nodes and edges in Canvas state so persistence and backend graph
  contracts remain complete; only the execution view is progressively filtered.
- Added non-terminal task polling publications so `pending` and `processing`
  updates refresh the source Skill node and Task evidence node before completion.
- Preserved task prompt, description, and progress detail in Canvas outputs.
- Added compact live text, parsed percentage progress bars, and media thumbnails to
  running node cards without changing their established geometry.
- Added regression coverage for progressive reveal, live card content, and
  pre-completion task publications.

## Validation

- Full frontend test suite:
  `cd ai-pic-frontend && npm run test` -> 427/427 passed.
- Focused progress/tracker suite:
  `npx tsx --test tests/productionCanvasProgressiveReveal.test.ts
tests/productionCanvasBusyActions.test.tsx
tests/productionCanvasExecutionTracker.test.tsx
tests/generationTaskTracker.test.ts` -> 21/21 passed.
- Focused Canvas interaction suite after geometry compatibility fixes -> 59/59
  passed.
- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 3 unrelated
  existing/concurrent-worktree warnings.
- Changed-file ESLint, `git diff --check`,
  `python scripts/check_repo_docs.py`, and
  `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- TypeScript output was checked for the changed Canvas and task-tracker files; no
  changed-file errors were reported. The repository-wide `npx tsc --noEmit`
  remains noisy in unrelated test files.
- Repository harness smoke:
  `canvas-dynamic-nodes-smoke-20260716T115700Z` opened authenticated
  `http://127.0.0.1:3000/canvas`. Chrome DevTools transport was unavailable, so
  the run is explicitly recorded as a passing Playwright fallback.
- Custom Playwright/system-Chrome execution proof:
  `artifacts/runs/canvas-dynamic-nodes-e2e-20260716T120000Z/`.
  The initial visible IDs were `brief`, `script`, and `script-task-9001`, while
  `storyboard` remained hidden. During polling, both running cards displayed
  `正在生成第 2/4 场（50%）`. After the second poll completed, `storyboard`
  appeared and `storyboard.plan` executed automatically.
- The custom browser run recorded five relevant API responses with HTTP 200, zero
  failed responses, and zero console warnings or errors. Progress and terminal
  screenshots are stored under the run's `screenshots/` directory.

## Next Steps

- Validate the same progressive behavior against a paid/provider-backed production
  generation when an operator intentionally wants to spend generation quota; this
  delivery used deterministic API interception for repeatable UI proof.
- The production-image build was not rerun because the dirty worktree contains
  unrelated in-progress backend changes that would make a whole-worktree image
  build an invalid proof for this staged frontend-only slice. Route, layout, auth,
  configuration, and hydration-sensitive code were not changed.

## Linked Commits

- This ledger is committed with the implementation.
