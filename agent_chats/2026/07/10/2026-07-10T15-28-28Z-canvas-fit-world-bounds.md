---
id: 2026-07-10T15-28-28Z-canvas-fit-world-bounds
date: "2026-07-10T15:28:28Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - interaction
  - viewport
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasInteractionControls.ts
  - ai-pic-frontend/tests/productionCanvasFit.test.tsx
summary: Fit the production canvas to actual positive and negative node bounds without including the broader interaction worktree.
---

# Canvas Fit World Bounds

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 让“适配”按当前节点的真实世界边界计算，而不是固定基准画布。
- 节点进入负坐标后，适配视图仍能把负坐标和正坐标节点一起带回可视区。
- 从现有混合交互 WIP 中只提交这一条完整行为链。

## Changes

- `useProductionCanvasInteractionControls` 使用 `getWorldBounds(state.nodes)` 计算 Fit 缩放。
- Fit viewport 根据 `minX` / `minY` 补偿负坐标，并保留 24px 视图内边距。
- 新增独立回归测试，将 Brief 放到 `x=-50`，验证真实世界适配 transform。
- 未改动现有 50% 最小缩放契约；超宽世界需要更小缩放时另行处理。

## Validation

- Detached worktree red check：旧实现得到 `translate(24px, 24px) scale(0.91)`，未补偿负 X；测试按预期失败。
- Detached worktree focused green check：`productionCanvasFit`、`productionCanvasState`、`ProductionCanvasBoard` 共 13 tests passed。
- Detached worktree `npm run lint`：0 errors，3 个既有 warnings。
- Detached worktree 标准 `npm run test`：除 `toastProvider.test.tsx` 外的用例均已输出通过，进程再次卡在该已知定时测试并手动终止。
- Detached worktree 排除 `toastProvider.test.tsx` 的完整前端集合：189 tests、40 suites passed。
- 内置浏览器使用 detached worktree 的 `HEAD + Fit patch` 临时前端 `http://localhost:3091/canvas`，连接现有 dev backend；Next Turbopack 因跨 worktree 的 node_modules 软链接拒绝启动后，改用同版本 webpack dev engine。
- 浏览器将 Brief 从 `x=40` 拖到 `x=-50`，世界边界更新为 `1310x600`；点击“适配”后 transform 为 `translate(50px, 24px) scale(0.52)`，默认生产节点全部回到可视区。
- 临时前端 `/canvas` 返回 200；Console warn/error 为空；截图：`artifacts/runs/canvas-fit-world-bounds-20260710T1524Z/negative-x-fit.png`。
- 浏览器已返回原始 8089 Canvas run，临时 3091 前端已停止。
- Detached worktree `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 继续拆分负坐标渲染偏移、键盘导航和焦点保持等现有 Canvas interaction WIP。
- 当真实用例需要适配超过 50% 最小缩放范围的世界时，再统一调整缩放、持久化和恢复契约。

## Linked Commits

- `6698bb4d` - `feat(canvas): persist render execution evidence`
- This commit (pending)
