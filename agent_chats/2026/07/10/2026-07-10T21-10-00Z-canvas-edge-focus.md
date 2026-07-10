---
id: 2026-07-10T21-10-00Z-canvas-edge-focus
date: "2026-07-10T21:10:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - edges
  - keyboard
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/tests/productionCanvasBoard.test.tsx
summary: Return keyboard focus to the infinite canvas after adding or removing edges.
---

# Canvas Edge Focus

## User Prompt

继续完善无限画布功能，保持原子化提交；可以拉起 dev_in_docker 并使用内置浏览器验证，当前整体链路仍未闭合。

## Goals

- 新增连线后将键盘焦点交还无限画布。
- 删除连线后保持相同的键盘操作连续性。
- 仅包装明确命令，不干扰便签或媒体参数输入框的编辑焦点。

## Changes

- Board 在调用既有 `handleAddEdge` 后统一调用 `focusCanvas`。
- Board 在调用既有 `handleRemoveEdge` 后统一调用 `focusCanvas`。
- 扩展 Board 连线回归，分别证明新增和删除后可直接用 ArrowRight 移动当前节点。
- `ProductionCanvasBoard.tsx` 保持 221 行，低于 250 行硬限制。

## Validation

1. Local checks:

- Board 专用测试：8 tests、1 suite passed。
- Board、Edge Controls、Keyboard Navigation、Board Task Summary、Toolbar Focus：17 tests、5 suites passed。
- 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：214 tests、51 suites passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- Scoped pre-commit：全部 passed，包括 Prettier、repository contracts、ledger enforcement 和 frontend lint。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build、TypeScript 与 `/canvas` route generation passed。

2. Browser or MCP validation:

- Environment: dev_in_docker backend and dependencies at `http://localhost:8000`; detached patched frontend at `http://localhost:3107` using Next webpack dev mode.
- Entry URL: `http://localhost:3107/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Engine: Chrome 150 over Chrome DevTools Protocol, controlled through Playwright `connectOverCDP`; Chrome DevTools MCP reconnect failed twice because an existing IPv4 listener returned HTTP 404.
- Restore: `GET /api/v1/production-canvas/runs/48d62cd56e1646c4b3f0c77c1a3cd4a6` returned 200 (`req-1783708918670-nohnwrrd`).
- Add path: added `Brief Skill -> Script Skill`; the edge existed, Surface was active, and ArrowRight moved Brief from `112px` to `128px`.
- Remove path: removed the same edge; the edge disappeared, Surface was active, and ArrowRight moved Brief from `128px` to `144px`.
- Persistence: autosave returned 200 (`req-1783708920431-ux8yzj4f`); authoritative restored state retained `Brief x=144` and contained zero copies of the temporary test edge.
- Console: no warning or error entries during restore, add, remove, and keyboard continuation.
- Evidence: `artifacts/runs/canvas-edge-focus-20260710T184200Z/edge-added.jpg` and `artifacts/runs/canvas-edge-focus-20260710T184200Z/edge-removed.jpg`.

3. Conflict signals and corrections:

- Chrome DevTools MCP remained unavailable after the required retry because `127.0.0.1:9222/json/version` returned HTTP 404.
- The independent Chrome IPv6 CDP path loaded the same run and exercised both commands in a real browser.
- The validation removed its temporary edge before autosave and then queried the saved state, preventing the browser proof from leaving a graph mutation behind.

## Next Steps

- Preserve input focus for continuous note/media editing while returning focus only from explicit side-panel commands.
- Audit node selection from side-panel lists and keyboard deletion against the same command boundary.

## Linked Commits

- `a89bf674` - `fix(canvas): retain focus after task selection`
- This commit (pending)
