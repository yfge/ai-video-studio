---
id: 2026-07-16T13-30-01Z-canvas-planned-edge-dedup
date: "2026-07-16T13:30:01Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - frontend
  - graph
  - browser-validation
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasDefinitionActions.ts
  - ai-pic-frontend/tests/productionCanvasPlanGraph.test.ts
summary: Deduplicate planned edges when progressive skill updates refresh a Production Canvas plan.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 保持 v2 规范图十一条 typed edges 稳定且唯一。
- 首个 Skill 执行状态刷新时不重复追加整组 planned edges。
- 让故事板浏览器链路在无 React key 警告的情况下完成。

## Changes

- 合并计划节点时按 `edgeId` 去重；无显式 ID 时使用完整端口 binding 作为稳定键。
- 新增首个 Skill 刷新回归测试，验证边数和边 ID 唯一性保持不变。

## Validation

- `cd ai-pic-frontend && ./node_modules/.bin/tsx --test tests/productionCanvasPlanGraph.test.ts`
  - focused plan-graph tests passed.
- Browser evidence:
  `artifacts/runs/canvas-v2-storyboard-20260716T1320Z/canvas_storyboard_e2e.json`
  - Playwright fallback passed after Chrome DevTools transport timed out.
  - 10 planned skills, 11 unique edges, 0 start-frame bindings, 0 end-frame bindings.
  - no page errors, no relevant console warnings or errors, and no failed API requests.
- `git diff --check`
  - passed.

## Next Steps

- Run the full frontend regression suite, lint, repository contract checks, and pre-commit.
- Update design/task evidence and integrate the isolated commits into the main worktree.

## Linked Commits

- This ledger is included in the planned-edge deduplication commit created for this task.
