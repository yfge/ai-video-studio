---
id: 2026-07-10T16-10-00Z-canvas-keyboard-viewport
date: "2026-07-10T16:10:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - keyboard
  - viewport
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasKeyboardViewport.test.tsx
summary: Add unmodified keyboard zoom and fit shortcuts to the production canvas viewport.
---

# Canvas Keyboard Viewport Controls

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 用键盘直接缩放画布，不依赖工具栏鼠标操作。
- 用 `0` 或 `Home` 将全部节点适配到当前视口。
- 保留浏览器的 Ctrl、Meta 和 Alt 修饰快捷键，不由画布劫持。

## Changes

- Controller 支持 `+`、`=` 放大和 `-` 缩小，复用现有视口缩放逻辑。
- Controller 支持 `0`、`Home` 适配全部节点，复用现有实际节点边界算法。
- 快捷键仅在没有 Alt、Ctrl、Meta 修饰时生效；方向键导航行为保持不变。
- 新增聚焦测试覆盖三种缩放按键、两种适配按键和浏览器修饰键透传。
- 选中节点定位、便签、删除和复制等后续快捷键不进入本提交。

## Validation

- Detached focused check：Viewport、Keyboard Navigation、Fit、Board 共 13 tests passed。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：193 tests、42 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- 内置浏览器使用 detached `HEAD + viewport shortcut patch` 前端 `http://localhost:3095/canvas`，连接开发后端。
- 首次启动未携带 `NEXT_PUBLIC_API_URL`，登录请求误发到 3095 并返回 `HTTP 404: Not Found`；按主开发环境配置重启后登录成功并进入画布。
- Surface 保持焦点；`=` 将 zoom 调到 110%，`Shift+=` 调到 120%，`-` 回到 110%，`Home` 将全链路适配到当前浏览器视口 54%。
- Console 无 warning/error；截图：`artifacts/runs/canvas-keyboard-viewport-20260710T1608Z/keyboard-fit.png`。
- 本切片只改变本地 viewport 状态，不产生业务 API 请求；登录 API 成功后画布真实路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交选中节点定位快捷键与工具栏焦点保持。
- 再拆便签新增、复制和删除快捷键，保持每条交互链可单独回滚。

## Linked Commits

- `680b5a60` - `feat(canvas): add keyboard navigation`
- This commit (pending)
