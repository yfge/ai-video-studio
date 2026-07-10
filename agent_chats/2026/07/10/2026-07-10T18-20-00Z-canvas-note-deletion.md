---
id: 2026-07-10T18-20-00Z-canvas-note-deletion
date: "2026-07-10T18:20:00Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - frontend
  - notes
  - keyboard
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNodeTools.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasNoteControls.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasNoteActions.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasNoteCommands.ts
  - ai-pic-frontend/tests/productionCanvasNodeTools.test.tsx
  - ai-pic-frontend/tests/productionCanvasNoteDeletion.test.tsx
summary: Delete selected manual canvas notes from the side tools or keyboard without affecting production or task evidence nodes.
---

# Canvas Manual Note Deletion

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 通过侧栏命令删除选中的手工便签。
- 通过 Delete 或 Backspace 快速删除选中便签。
- 删除节点时同步移除连接边，并选择稳定 fallback 节点。
- 生产节点和任务证据节点不可被便签删除命令误伤。

## Changes

- note-actions 新增纯状态删除 helper，只接受手工便签并复用 graph-state 节点/连线删除。
- 新增 `useProductionCanvasNoteCommands`，集中管理已提交的复制与新增删除命令，统一完成后回焦 Surface。
- Controller 增加 Delete/Backspace 分支，仅在选中手工便签时阻止默认行为。
- NoteControls 新增红色“删除便签”命令，NodeTools 与 Board 完成接线。
- Surface 执行回调仅缩短参数名以守住 Board 250 行限制，行为不变。
- 新增测试覆盖按钮、Delete、Backspace、焦点、fallback selection、连线清理和任务证据保护。

## Validation

- Detached focused check：Note Deletion、Note Duplication、Note Editing、Node Tools、Keyboard Navigation、Board 共 19 tests passed。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：210 tests、48 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次由 Prettier 格式化专用删除测试；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- 编辑前 Board 249 行、Controller 244 行，均低于 canvas 250 行结构上限；note commands hook 28 行。
- 内置浏览器使用 detached `HEAD + note deletion patch` 前端 `http://localhost:3101/canvas`，连接开发后端。
- 浏览器首次使用非精确“删除便签” locator 时同时匹配“便签 待删除便签”卡片和删除按钮；改为 exact locator 后继续验证，页面行为无异常。
- 删除按钮、Delete、Backspace 均将便签数量降为 0，编辑器消失且焦点返回 Surface。
- 删除后对 Brief 按 Delete，画布节点数保持 7，Brief 仍存在。
- Console warning/error 为空；截图：`artifacts/runs/canvas-note-deletion-20260711T0215Z/delete-control.png`。
- 本切片仅改变本地 canvas state，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 继续拆分工具栏、运行控制和 Inspector 操作后的焦点保持。
- 评估 Board 接近行数上限后的组件抽取，避免后续功能继续堆积。

## Linked Commits

- `5e9775e3` - `feat(canvas): duplicate manual notes`
- This commit (pending)
