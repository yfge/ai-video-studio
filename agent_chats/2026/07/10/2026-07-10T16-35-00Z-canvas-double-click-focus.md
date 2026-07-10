---
id: 2026-07-10T16-35-00Z-canvas-double-click-focus
date: "2026-07-10T16:35:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - interaction
  - accessibility
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasSurface.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasDoubleClick.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasDoubleClickFocus.test.tsx
summary: Select and center production canvas nodes on double click without consuming blank-canvas double clicks.
---

# Canvas Node Double-Click Focus

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 双击画布节点时直接选中并将其定位到视口中心。
- 复用现有定位算法并保留当前 zoom。
- 空白区域双击保持无操作，为后续便签命令保留事件入口。

## Changes

- Surface 新增双击事件入口，不改变滚轮、拖拽和节点执行行为。
- 新增小型节点命中 helper，从 target、composed path 或坐标命中中解析画布 node id。
- Controller 的定位命令可接收明确 node id，同时更新选中状态并将焦点交回 Surface。
- Board 只在双击命中节点时调用定位；空白双击不创建任何内容。
- 工具栏定位改为显式无参调用，避免 React MouseEvent 被误当作 node id。
- 新增测试覆盖节点双击选中居中、Surface 焦点和空白双击无副作用。
- 空白双击新增便签和大型 Board 拆分继续留在后续 WIP，不进入本提交。

## Validation

- Detached focused check：Double Click Focus、Focus Selected、Viewport、Keyboard Navigation、Fit、Board 共 18 tests passed。
- 首次 focused check 暴露工具栏 `onClick={handleFocusSelectedNode}` 将 MouseEvent 当作 node id，导致定位失效；改为显式无参调用后复跑通过。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：198 tests、44 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次由 Prettier 格式化 Board 和双击 helper；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- Board 243 行、Surface 101 行、Controller 206 行，均低于 canvas 250 行结构上限。
- 内置浏览器使用 detached `HEAD + double-click focus patch` 前端 `http://localhost:3097/canvas`，连接开发后端。
- 双击 Report 后 viewport 从 `translate(0px, 0px) scale(1)` 更新为 `translate(-718px, -23px) scale(1)`，Report 呈选中态且 Surface 保持焦点。
- 在空白区域双击后 viewport 不变，manual note 数量保持 0。
- Console warning/error 为空；截图：`artifacts/runs/canvas-double-click-focus-20260711T0032Z/report-double-click-centered.png`。
- 本切片仅改变本地 viewport 和 selection 状态，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交空白双击新增便签，并验证 viewport/zoom 坐标换算。
- 再拆便签复制和删除快捷键，保持交互链可独立回滚。

## Linked Commits

- `884e94fe` - `feat(canvas): focus selected node`
- This commit (pending)
