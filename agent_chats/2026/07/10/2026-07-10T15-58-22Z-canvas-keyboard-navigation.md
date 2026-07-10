---
id: 2026-07-10T15-58-22Z-canvas-keyboard-navigation
date: "2026-07-10T15:58:22Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - keyboard
  - accessibility
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasSurface.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasKeyboard.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasKeyboardNavigation.test.tsx
summary: Add focused arrow-key node movement and empty-selection viewport panning to the production canvas.
---

# Canvas Keyboard Navigation

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 节点选择后可直接用方向键进行精确移动。
- `Shift + 方向键` 提供更大的移动步长，浏览器修饰键组合不被画布劫持。
- `Escape` 清空选择后，方向键改为平移 viewport。
- 节点点击后将焦点交回画布，使键盘链路真实可达。

## Changes

- Surface 变为带可访问名称的可聚焦 region，并接收现有 Controller 键盘处理器。
- 新增 `productionCanvasKeyboard`，统一 16px / 64px nudge 和“选中节点移动、空选择平移”状态变换。
- Controller 处理方向键与 Escape，并允许真正的空选择状态。
- NodeCard 点击选择节点后把焦点返回 Surface。
- 新增聚焦测试覆盖普通移动、Shift 加速、Meta 组合键不劫持、Escape 和空选择平移。
- Home/F/N/Delete/复制等后续快捷键仍留在未提交 WIP，不进入本提交。

## Validation

- Detached worktree focused check：Keyboard Navigation、Fit、State、Board 共 14 tests passed。
- 当前 interaction WIP focused check：现有 Keyboard、Keyboard Navigation、Fit 共 21 tests passed。
- Detached worktree 排除已知 `toastProvider.test.tsx` 的完整前端集合：190 tests、41 suites passed。
- Detached worktree `npm run lint`：0 errors，3 个既有 warnings。
- Detached worktree scoped pre-commit 全部 passed；主工作树首次运行时 repo-contracts 读取了未暂存的 266 行后续 Controller WIP，而 index 版本仅 168 行，因此以精确 detached 状态复核。
- 内置浏览器使用 detached `HEAD + keyboard patch` 临时前端 `http://localhost:3094/canvas`。
- 点击 Script 后 Surface 获得焦点；ArrowRight 将节点 `left` 从 270px 移到 286px，Shift+ArrowRight 再移到 350px，Meta+ArrowRight 保持 350px。
- Escape 后 Script 不再选中；ArrowRight 与 Shift+ArrowDown 将 viewport 更新为 `translate(16px, 64px)`。
- Console warn/error 为空；截图：`artifacts/runs/canvas-keyboard-nav-20260710T1602Z/node-nudge-and-pan.png`。
- 浏览器已恢复原始 8089 run `48d62cd56e1646c4b3f0c77c1a3cd4a6`，页面仍包含 Render #122。
- Detached worktree `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 分别提交键盘缩放/Fit/定位和便签快捷键，保持每条交互链独立。
- 继续拆分 Toolbar 焦点保持，避免鼠标操作打断键盘工作流。

## Linked Commits

- `b3e543a5` - `refactor(canvas): extract rendering surface`
- This commit (pending)
