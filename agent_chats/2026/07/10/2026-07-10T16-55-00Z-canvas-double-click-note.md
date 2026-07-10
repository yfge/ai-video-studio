---
id: 2026-07-10T16-55-00Z-canvas-double-click-note
date: "2026-07-10T16:55:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - interaction
  - notes
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasDoubleClick.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasDoubleClickFocus.test.tsx
  - ai-pic-frontend/tests/productionCanvasDoubleClickNote.test.tsx
summary: Create a selected manual note at the exact blank-canvas double-click location across pan and zoom states.
---

# Canvas Blank Double-Click Note

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 双击画布空白区域时，在点击位置中心新增手工便签。
- 坐标换算正确处理 viewport 平移、zoom clamp 和负坐标渲染原点。
- 节点双击仍只执行节点定位，不额外创建便签。
- 新增后保持 Surface 焦点，键盘操作可连续进行。

## Changes

- 双击 helper 新增屏幕坐标到 world 坐标的反算，并以便签中心对齐点击点。
- Board 在双击未命中节点时按换算坐标新增便签；命中节点时仍优先定位。
- Controller 的新增便签命令可接收明确 world 坐标，并在完成后把焦点交回 Surface。
- 工具栏“添加便签”改为显式无参调用，避免 React MouseEvent 被误当作坐标。
- 更新节点双击测试，确认节点双击不会创建便签；新增专用测试覆盖默认位置、pan、zoom clamp 和工具栏回归。
- 便签编辑、复制、删除和 Board 大型拆分继续留在后续 WIP，不进入本提交。

## Validation

- Detached focused check：Double Click Note、Double Click Focus、Focus Selected、Viewport、Keyboard Navigation、Fit、Board 共 21 tests passed。
- 初始坐标单测使用 zoom=2 却按未 clamp 值计算；helper 按画布规则 clamp 到 1.6，修正预期后通过。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：201 tests、45 suites passed；坐标公式修正后完整集合再次通过。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次由 Prettier 格式化双击 helper 和专用测试；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- Board 在压缩双击 handler 后为 247 行，Controller 207 行，均低于 canvas 250 行结构上限。
- 内置浏览器使用 detached `HEAD + blank double-click note patch` 前端 `http://localhost:3098/canvas`，连接开发后端。
- Playwright locator 的 position 参数在当前内置接口中被忽略，首次实际双击发生在 Surface 中心；改用浏览器坐标级双击后获得可信点位证据。
- 初始公式重复加入 `worldBounds.minX`，在 Brief=-24、zoom=53% 时产生 -12.51px 横向偏差；渲染中的 node offset 与 world transform 已抵消该 bounds，移除重复补偿后修正。
- 最终在屏幕 `(879,530)` 双击，便签中心为 `(879.21,530.12)`，仅剩亚像素渲染误差；便签选中且 Surface 保持焦点。
- Console warning/error 为空；截图：`artifacts/runs/canvas-double-click-note-20260711T0050Z/negative-bounds-note.png`。
- 本切片仅改变本地 canvas state，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交便签文本编辑和空标题展示。
- 再拆便签复制、删除与键盘快捷键，保持交互链可独立回滚。

## Linked Commits

- `1260aa7c` - `feat(canvas): focus nodes on double click`
- This commit (pending)
