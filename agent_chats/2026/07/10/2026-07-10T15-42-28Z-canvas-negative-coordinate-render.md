---
id: 2026-07-10T15-42-28Z-canvas-negative-coordinate-render
date: "2026-07-10T15:42:28Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - coordinates
  - edges
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx
  - ai-pic-frontend/tests/productionCanvasFit.test.tsx
summary: Normalize negative canvas node and edge coordinates while preserving the logical viewport transform.
---

# Canvas Negative Coordinate Render

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 让负坐标节点在 world 容器内使用非负局部坐标渲染。
- 让 SVG 连线与节点使用同一坐标偏移，避免负坐标路径被裁切或错位。
- 保持 viewport 的逻辑坐标语义，使 Fit、pan 和 zoom 不重复补偿 `minX/minY`。

## Changes

- Canvas 节点卡片按 `node.x - minX`、`node.y - minY` 归一化到 world 局部坐标。
- SVG edge path 使用相同的 world bounds 偏移，并由 bounds 统一提供尺寸和原点。
- world transform 在 viewport translate/scale 之后追加逻辑 `minX/minY` translate，恢复原始世界坐标语义。
- 扩展 Fit 回归测试，同时断言 world transform、Brief 局部位置和 `brief-script` 连线路径。
- 同步修正未提交 Surface/键盘测试 WIP，但这些文件或额外 hunk 不进入本提交。

## Validation

- Detached worktree red check：旧实现仍为 `translate(64px, 24px) scale(0.79)`，Brief 为 `left:-50px`，未包含逻辑坐标 translate；升级测试按预期失败。
- Detached worktree focused green check：`productionCanvasFit`、`productionCanvasState`、`ProductionCanvasBoard` 共 13 tests passed。
- 当前 interaction WIP focused check：Fit、Graph、Keyboard 共 39 tests passed，证明 Surface 同步后未破坏后续交互工作。
- Detached worktree 排除已知 `toastProvider.test.tsx` 的完整前端集合：189 tests、40 suites passed。
- Detached worktree `npm run lint`：0 errors，3 个既有 warnings。
- 内置浏览器使用 detached `HEAD + patch` 临时前端 `http://localhost:3092/canvas`，连接现有 dev backend。
- 浏览器将 Brief 拖到逻辑 `x=-50`：world 为 `1310x600`，Brief 局部 `left:0px`，`brief-script` path 为 `M 170 171 C 245 171 245 107 320 107`。
- 点击“适配”后 transform 为 `translate(50px, 24px) scale(0.52) translate(-50px, 0px)`，节点与连线完整可见；Console warn/error 为空。
- 截图：`artifacts/runs/canvas-negative-render-20260710T1540Z/negative-node-edge-fit.png`。
- 临时 3092 前端已停止；验证 tab 返回 8089 时因端口级 localStorage 登录隔离被重定向到登录页，不是应用回归。
- Detached worktree `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 继续拆分当前 Canvas Surface、键盘导航和焦点保持 WIP。
- 当真实画布需要低于 50% 的 Fit 缩放时，再统一调整缩放、持久化和恢复契约。

## Linked Commits

- `395d457a` - `fix(canvas): fit actual node bounds`
- This commit (pending)
