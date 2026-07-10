---
id: 2026-07-10T15-50-56Z-canvas-surface-extraction
date: "2026-07-10T15:50:56Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - refactor
  - surface
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasSurface.tsx
summary: Extract the committed canvas rendering surface without changing pointer, viewport, node, or edge behavior.
---

# Canvas Surface Extraction

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 从 250 行上限的 Board 中抽出已提交的 Canvas 渲染面。
- 保持 pointer、wheel、viewport、节点执行、选择和连线行为完全等价。
- 为后续键盘、焦点和任务同步功能建立可独立提交的组件边界。

## Changes

- 新增 `ProductionCanvasSurface`，承接 canvas 容器、world transform、节点和 SVG 连线渲染。
- Board 只负责向 Surface 传递现有状态与事件处理器，不新增任何交互语义。
- Board 从 250 行降至 223 行，Surface 为 91 行，均满足仓库文件规模约束。
- 当前工作树中更后续的 Surface 键盘/焦点 WIP 保持未暂存。

## Validation

- Detached worktree focused check：`productionCanvasFit`、`productionCanvasState`、`ProductionCanvasBoard` 共 13 tests passed。
- Detached worktree 排除已知 `toastProvider.test.tsx` 的完整前端集合：189 tests、40 suites passed。
- Detached worktree `npm run lint`：0 errors，3 个既有 warnings。
- 内置浏览器使用 detached `HEAD + extraction patch` 临时前端 `http://localhost:3093/canvas`；因临时 worktree 使用外部 node_modules 软链接，明确使用同版本 webpack dev engine。
- 浏览器将 Brief 拖到 `x=-50` 后点击“适配”：world transform、Brief 局部位置和 `brief-script` path 与抽取前完全一致。
- Console warn/error 为空；截图：`artifacts/runs/canvas-surface-extract-20260710T1553Z/drag-fit-equivalence.png`。
- 浏览器已在 8089 重新登录并恢复原始 run `48d62cd56e1646c4b3f0c77c1a3cd4a6`，页面仍包含 Render #122。
- Detached worktree `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 在独立 Surface 边界上继续拆分键盘导航、双击定位和焦点保持行为。
- 再拆分 Toolbar / SidePanel 时继续保持行为提交与纯重构提交分离。

## Linked Commits

- `29b542aa` - `fix(canvas): align negative coordinate rendering`
- This commit (pending)
