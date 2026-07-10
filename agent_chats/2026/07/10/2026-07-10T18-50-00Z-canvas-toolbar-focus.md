---
id: 2026-07-10T18-50-00Z-canvas-toolbar-focus
date: "2026-07-10T18:50:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - toolbar
  - keyboard
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasToolbar.tsx
  - ai-pic-frontend/tests/productionCanvasToolbarFocus.test.tsx
summary: Extract the canvas toolbar and preserve keyboard navigation after local viewport commands.
---

# Canvas Toolbar Focus

## User Prompt

继续完善无限画布功能，保持原子化提交；可以拉起 dev_in_docker 并使用内置浏览器验证，当前整体链路仍未闭合。

## Goals

- 从 Board 抽出独立工具栏，降低画布主组件的结构压力。
- 工具栏执行新增便签、缩放、定位选中、适配和重置后，将焦点返回 Surface。
- 保证用户点击视口命令后可以直接继续使用方向键操作画布。

## Changes

- 新增 `ProductionCanvasToolbar`，承接本地画布命令和既有运行控制。
- 工具栏本地命令执行后统一调用 `onReturnFocus`，不改变保存、恢复和复制运行链接的既有行为。
- Board 通过 `focusCanvas` 接线并从 249 行降至 206 行；Toolbar 为 102 行。
- 新增组件测试，覆盖缩放、适配和重置后的 Surface 回焦。

## Validation

- Detached focused check：Board、Focus Selected、Keyboard Navigation、Keyboard Viewport、Toolbar Focus 共 16 tests、5 suites passed。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：211 tests、49 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次由 Prettier 格式化新增测试；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- 内置浏览器使用 detached 前端 `http://localhost:3102/canvas`，连接开发后端。
- 点击放大后 Surface 获得焦点，world scale 为 1.1，ArrowRight 将 Script 左移位置从 270px 更新为 286px。
- 点击适配后 Surface 获得焦点，world transform 为 `translate(24px, 24px) scale(0.54)`，ArrowRight 将 Script 更新为 302px。
- 点击重置后 Surface 获得焦点，world 恢复 scale 1，ArrowRight 将 Brief 更新为 56px。
- Console warning/error 为空；截图：`artifacts/runs/canvas-toolbar-focus-20260711T0245Z/reset-keyboard-continuity.png`。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 为运行控制中的保存、恢复和复制链接补齐异步结束后的 Surface 回焦。
- 继续收口 Inspector 和节点执行动作后的键盘连续性。

## Linked Commits

- `fd964a2a` - `feat(canvas): delete manual notes`
- This commit (pending)
