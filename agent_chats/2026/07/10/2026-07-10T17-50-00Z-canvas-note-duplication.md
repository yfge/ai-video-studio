---
id: 2026-07-10T17-50-00Z-canvas-note-duplication
date: "2026-07-10T17:50:00Z"
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
  - ai-pic-frontend/tests/productionCanvasNodeTools.test.tsx
  - ai-pic-frontend/tests/productionCanvasNoteDuplication.test.tsx
summary: Duplicate selected manual canvas notes from the side tools or Cmd/Ctrl+D while preserving browser shortcuts elsewhere.
---

# Canvas Manual Note Duplication

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- 通过侧栏命令复制选中的手工便签。
- 通过 `Cmd+D` / `Ctrl+D` 快速复制选中便签。
- 副本保留标题、内容和尺寸，以 24px 偏移显示并成为当前选择。
- 生产节点和任务证据节点不拦截浏览器的复制/书签快捷键。

## Changes

- 新增纯状态复制 helper，只接受手工便签并生成无冲突的新 note id。
- 副本保留标题、内容、宽高，位置在原便签基础上横纵各偏移 24px。
- Controller 统一暴露复制命令，按钮和快捷键共用同一路径，完成后焦点返回 Surface。
- `Cmd+D` / `Ctrl+D` 仅在选中手工便签且没有 Alt/Shift 时拦截；其他节点保持默认浏览器行为。
- NoteControls 新增“复制便签”，NodeTools 与 Board 完成接线。
- 为守住 Board 250 行限制，内联既有 reset handler 并缩短双击 viewport 局部处理；行为不变。
- 新增专用测试覆盖按钮、Cmd+D、文本尺寸、24px 偏移、焦点和任务证据保护。
- 便签删除及 Delete/Backspace 快捷键继续留在后续 WIP，不进入本提交。

## Validation

- Detached focused check：Note Duplication、Note Editing、Double Click Note、Node Tools、Keyboard Navigation、Board 共 19 tests passed。
- Detached 完整前端集合排除已知挂起的 `toastProvider.test.tsx`：207 tests、47 suites passed。
- Detached `npm run lint`：0 errors，3 个既有 warnings。
- Detached scoped pre-commit：首次由 Prettier 格式化复制 helper 和专用测试；重新暂存后全部 passed，包括 repository contracts、ledger enforcement 和 frontend lint。
- 编辑前 Board 249 行、Controller 239 行，均低于 canvas 250 行结构上限。
- 内置浏览器使用 detached `HEAD + note duplication patch` 前端 `http://localhost:3100/canvas`，连接开发后端。
- 编辑后的 note-1 经按钮复制为 note-2，再经 Cmd+D 复制为 note-3；三者坐标依次为 `(272,232)`、`(296,256)`、`(320,280)`。
- 三张便签标题均为“复用检查点”，内容均为“复制后继续记录第二轮判断。”，宽高均为 190x96；复制后焦点保持 Surface。
- Console warning/error 为空；截图：`artifacts/runs/canvas-note-duplication-20260711T0145Z/button-and-command-d.png`。
- 本切片仅改变本地 canvas state，不产生业务 API 请求；登录成功后真实画布路径可用。
- Detached `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`：backend/frontend production images built locally without push；Next production build 与 TypeScript passed。

## Next Steps

- 独立提交便签删除按钮与 Delete/Backspace 快捷键。
- 验证任务证据节点和生产节点不会被删除快捷键误伤。

## Linked Commits

- `73bab6c7` - `feat(canvas): edit manual notes`
- This commit (pending)
