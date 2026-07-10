---
id: 2026-07-10T19-10-00Z-canvas-run-controls-focus
date: "2026-07-10T19:10:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - persistence
  - keyboard
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasToolbar.tsx
  - ai-pic-frontend/tests/productionCanvasToolbarFocus.test.tsx
summary: Return keyboard focus to the infinite canvas after save and restore commands.
---

# Canvas Run Controls Focus

## User Prompt

继续完善无限画布功能，保持原子化提交；可以拉起 dev_in_docker 并使用内置浏览器验证，当前整体链路仍未闭合。

## Goals

- 保存和恢复画布后保持键盘操作连续。
- Run ID 输入框按 Enter 恢复后同样回焦 Surface。
- 复用 Toolbar 已有回焦边界，不扩大 Board 或 RunControls 的职责。

## Changes

- Toolbar 将保存和恢复回调纳入现有 `runCommand`，动作触发后统一调用 `onReturnFocus`。
- Run ID 输入框的 Enter 恢复沿用同一个包装回调，不新增状态或抽象。
- 扩展 Toolbar 专用测试，覆盖保存、按钮恢复、Enter 恢复以及后续键盘事件。

## Validation

1. Local checks:

- Toolbar 专用测试：2 tests、1 suite passed。
- Board、Persistence、RunControls、Toolbar Focus：18 tests、4 suites passed。
- 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：212 tests、49 suites passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- Scoped pre-commit：全部 passed，包括 Prettier、repository contracts、ledger enforcement 和 frontend lint。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build、TypeScript 与 `/canvas` route generation passed。

2. Browser or MCP validation:

- Environment: dev_in_docker backend and dependencies at `http://localhost:8000`; detached patched frontend at `http://localhost:3103` using Next webpack dev mode.
- Entry URL: `http://localhost:3103/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Engine: Codex in-app Browser; this run is not labelled Chrome DevTools verification.
- Save path: selected Brief, clicked `保存画布`, status became `已保存`, Surface was active, and ArrowRight moved Brief from `80px` to `96px`.
- Restore path: clicked `恢复画布`, status became `已恢复`, Surface remained active, and ArrowRight moved Brief from `96px` to `112px`.
- Network: save `PUT /api/v1/production-canvas/runs/48d62cd56e1646c4b3f0c77c1a3cd4a6/state` returned 200 (`req-1783705112608-jotk3t11`); restore `GET /api/v1/production-canvas/runs/48d62cd56e1646c4b3f0c77c1a3cd4a6` returned 200 (`req-1783705166463-qi7h8ah1`).
- Console: no warning or error entries; only React DevTools and HMR informational logs.
- Evidence: `artifacts/runs/canvas-run-focus-20260711T0140Z/save-restore-keyboard-continuity.jpg`.

3. Conflict signals and corrections:

- `scripts/harness/bootstrap_worktree.sh --mode lite` could not start because detached worktree lacks untracked `docker/.env.lite`; reused the main frontend dependency directory without starting a duplicate stack.
- Turbopack rejected the cross-worktree `node_modules` link; reran the exact patched frontend with Next `--webpack`, then completed the browser path against the running Docker backend.

## Next Steps

- Continue closing Inspector and node execution actions that leave keyboard focus outside the Surface.
- Audit remaining user-visible canvas commands against the same click-action-keyboard sequence.

## Linked Commits

- `5f4e5224` - `feat(canvas): retain toolbar focus`
- This commit (pending)
