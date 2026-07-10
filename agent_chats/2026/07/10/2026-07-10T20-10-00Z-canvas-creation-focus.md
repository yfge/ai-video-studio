---
id: 2026-07-10T20-10-00Z-canvas-creation-focus
date: "2026-07-10T20:10:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - creation
  - keyboard
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/tests/productionCanvasCreationFocus.test.tsx
summary: Return keyboard focus to the infinite canvas after whole-canvas creation.
---

# Canvas Creation Focus

## User Prompt

继续完善无限画布功能，保持原子化提交；可以拉起 dev_in_docker 并使用内置浏览器验证，当前整体链路仍未闭合。

## Goals

- 整体创建启动异步计划后立即将键盘焦点交还无限画布。
- 计划节点到达并成为当前选择后，无需再次点击即可继续键盘操作。
- 复用 Board 已有 `focusCanvas` 边界，不修改规划 API 或 ChatBar 职责。

## Changes

- Board 的整体创建回调在启动既有异步 `createFromPrompt` 后统一调用 `focusCanvas`。
- 新增创建回焦回归测试，证明计划创建后首个选中节点可直接通过 ArrowRight 移动。
- `ProductionCanvasBoard.tsx` 保持 214 行，低于 250 行硬限制。

## Validation

1. Local checks:

- 创建回焦专用测试：1 test、1 suite passed。
- Board、Creation Focus、Execution Focus、Focus Selected、Persistence、Toolbar Focus：17 tests、6 suites passed。
- 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：214 tests、51 suites passed。
- `cd ai-pic-frontend && npm run lint`：0 errors，3 个既有 warnings。
- Scoped pre-commit：全部 passed，包括 Prettier、repository contracts、ledger enforcement 和 frontend lint。
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build、TypeScript 与 `/canvas` route generation passed。

2. Browser or MCP validation:

- Environment: dev_in_docker backend and dependencies at `http://localhost:8000`; detached patched frontend at `http://localhost:3105` using Next webpack dev mode.
- Entry URL: `http://localhost:3105/canvas`; created run URL: `http://localhost:3105/canvas?run_id=303a2f09ddc141e595375ca977caf8c5`.
- Engine: Chrome 150 over Chrome DevTools Protocol, controlled through Playwright `connectOverCDP`; Chrome DevTools MCP reconnect failed twice because an existing IPv4 listener returned HTTP 404.
- Creation path: clicked `整体创建`; Surface was active immediately and remained active after the asynchronous plan completed.
- Network: plan returned 200 (`req-1783707345631-3721tv0t`), automatic `brief.compose` execution returned 200 (`req-1783707345659-qwzvj8k8`), run read returned 200 (`req-1783707345674-x7dddkb6`), and autosave returned 200 (`req-1783707347459-stox8qjd`).
- Result: selected `Brief Skill` moved from `80px` to `96px` with ArrowRight; the persisted state contained 19 nodes and retained the new Skill plan plus `Brief Skill x=96`.
- Console: no warning or error entries during creation and keyboard continuation.
- Evidence: `artifacts/runs/canvas-creation-focus-20260710T181500Z/creation-keyboard-continuity.jpg`.

3. Conflict signals and corrections:

- Initial overlap assumption: browser automation could not center-click a partially covered Report node, suggesting automatic node placement caused the overlap.
- Contradicting evidence: the plan kept `Render x=2610 / Report x=3170`; the reused Run's saved manual positions were `Report x=2580 / Render x=2658`.
- Correction: preserved user-authored layout and did not add automatic restore-time repositioning.
- Initial autosave assumption: a truncated request log started with the seven default nodes and appeared to overwrite the new plan.
- Contradicting evidence: the authoritative saved state contained all 19 nodes, including the generated Skill layer and the moved Brief node.
- Correction: kept the existing append-and-autosave flow unchanged and limited the fix to the proven creation-focus gap.

## Next Steps

- Wire the task-summary commands into the same Surface focus boundary.
- Continue the whole-canvas workflow audit with current server state and complete request bodies before changing persistence behavior.

## Linked Commits

- `9a774269` - `fix(canvas): retain focus after node execution`
- This commit (pending)
