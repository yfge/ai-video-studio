---
id: 2026-07-10T16-20-00Z-canvas-focus-selected
date: "2026-07-10T16:20:00Z"
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
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasFocusSelected.test.tsx
summary: Center the production canvas on its selected node from keyboard or toolbar while retaining canvas focus.
---

# Canvas Focus Selected Node

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 快速将远离当前视口的选中节点定位到画布中心。
- 同时支持键盘与工具栏命令，并保持后续键盘操作连续。
- 空选择时不执行无意义定位，也不劫持 `F`。

## Changes

- Controller 新增选中节点居中命令，基于真实 Surface 尺寸和当前 zoom 计算 viewport。
- Surface 聚焦时按 `F` 定位选中节点；Alt、Ctrl、Meta 组合键继续透传。
- 现有工具栏新增“定位选中”命令，空选择时禁用。
- 键盘或工具栏定位后焦点返回无限画布 Surface。
- 新增聚焦测试覆盖 F 定位、工具栏定位、焦点回归和空选择状态。
- 大型 Board 拆分、双击定位和便签增删复制仍留在后续 WIP，不进入本提交。

## Validation

- Detached focused check：Focus Selected、Viewport、Keyboard Navigation、Fit、Board 共 16 tests passed。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：196 tests、43 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次仅由 Prettier 格式化 Controller；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- Board 234 行、Controller 206 行，均低于 canvas 250 行结构上限。
- 内置浏览器使用 detached `HEAD + focus selected patch` 前端 `http://localhost:3096/canvas`，连接开发后端。
- 选择 Report 后按 `F`，viewport 从 `translate(0px, 0px) scale(1)` 更新为 `translate(-718px, -23px) scale(1)`，Surface 保持焦点。
- 先适配到 54% 再点击“定位选中”，viewport 更新为 `translate(-219px, 116px) scale(0.54)`，焦点返回 Surface；Escape 后命令禁用。
- Console warning/error 为空；截图：`artifacts/runs/canvas-focus-selected-20260711T0018Z/report-centered.png`。
- 本切片仅改变本地 viewport 状态，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交节点双击定位，复用本次居中命令。
- 再拆便签新增、复制和删除快捷键，保持交互链可独立回滚。

## Linked Commits

- `b8a50edc` - `feat(canvas): add viewport keyboard shortcuts`
- This commit (pending)
