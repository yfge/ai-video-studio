---
id: 2026-07-10T17-20-00Z-canvas-note-editing
date: "2026-07-10T17:20:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - notes
  - editing
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasElements.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeCard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeTools.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNoteControls.tsx
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/tests/productionCanvasNodeTools.test.tsx
  - ai-pic-frontend/tests/productionCanvasNoteEditing.test.tsx
summary: Edit manual canvas note titles and details while keeping blank titles accessible and stable.
---

# Canvas Manual Note Editing

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 选中手工便签后，可在侧栏编辑标题和内容。
- 编辑结果立即同步到画布卡片和 Inspector。
- 空白或纯空格标题保留原始输入值，但展示稳定的“未命名便签”。
- 生产节点和任务证据节点不暴露手工便签编辑器。

## Changes

- 新增仅包含标题与内容字段的 `ProductionCanvasNoteControls`，只对手工便签渲染。
- Controller 新增通用节点 patch 命令，复用既有 graph-state 更新函数。
- Board 与 NodeTools 接通节点更新命令，不引入复制、删除或 SidePanel 重构。
- CanvasNodeCard 和 CanvasInspector 统一使用既有 display-title helper，空标题显示“未命名便签”。
- 更新 NodeTools 测试调用契约，新增专用测试覆盖标题、内容、空标题和生产节点隔离。
- 便签复制、删除及其键盘快捷键继续留在后续 WIP，不进入本提交。

## Validation

- Detached focused check：Note Editing、Double Click Note、Double Click Focus、Node Tools、Board 共 17 tests passed。
- 初始测试使用 `fireEvent.change`，在当前 Node/JSDOM 组合中未触发 React 文本输入；补充 InputEvent 后仍不触发。组件改用单一 `onInput` 后，测试与真实浏览器输入均通过，且避免同时绑定两个事件导致重复更新。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：204 tests、46 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：全部 passed，包括 Prettier、repository contracts、ledger enforcement 和 frontend lint。
- 编辑前 Board 249 行、Controller 218 行，其余 canvas 文件均低于 250 行结构上限。
- 内置浏览器使用 detached `HEAD + note editing patch` 前端 `http://localhost:3099/canvas`，连接开发后端。
- 输入“手工风险确认”和“需要人工确认付款镜头。”后，卡片 aria-label、卡片文本、Inspector 和受控输入值同步。
- 标题改为三个空格后，输入值仍为三个空格，卡片与 Inspector 均显示“未命名便签”。
- 选择 Report 后标题、内容字段均消失，焦点返回 Surface。
- Console warning/error 为空；截图：`artifacts/runs/canvas-note-editing-20260711T0118Z/blank-title-editor.png`。
- 本切片仅改变本地 canvas state，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交便签复制命令与快捷键。
- 再拆便签删除命令与键盘保护，保持任务证据节点不可误删。

## Linked Commits

- `633fb44d` - `feat(canvas): add notes on blank double click`
- This commit (pending)
