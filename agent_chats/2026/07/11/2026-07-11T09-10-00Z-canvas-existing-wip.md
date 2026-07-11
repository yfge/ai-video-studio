---
id: 2026-07-11T09-10-00Z-canvas-existing-wip
date: "2026-07-11T09:10:00Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - delivery
related_paths:
  - ai-pic-frontend/src/components/features/canvas
  - ai-pic-frontend/tests
summary: Records one increment of the production infinite canvas implementation and its validation.
---

## User Prompt

先提交现有变更

## Goals

- 把当前混合 worktree 中的无限画布实现整理为可验证的原子提交。
- 保留任务状态同步、组件拆分、键盘与指针交互、保存恢复和错误作用域行为。
- 修复现有 WIP 中阻断 TypeScript 构建和画布回归测试的问题。
- 不把独立后端任务分发、数据库迁移或 toast 测试稳定性改动混入画布提交。

## Changes

- 将 Production Canvas 的 planning header、side panel、info panels 和 task sync 拆为独立组件或 hook，保持 `ProductionCanvasBoard` 为组合层。
- 在画布节点和检查器中展示任务状态，支持单任务与任务摘要刷新、错误作用域、busy 锁和任务深链。
- 收口滚轮平移/缩放、中键与 Alt 拖动画布、节点拖动、双击定位、键盘导航、便签编辑/复制/删除和焦点返回行为。
- 保留手动便签删除 helper 和复制尺寸契约，避免现有 hook、测试和 TypeScript 编译断裂。
- 修正带 Ctrl/Meta/Alt 的浏览器缩放快捷键不被画布吞掉，并让非便签节点的 Cmd+D 保持浏览器默认行为。
- 更新拆分后的画布测试与 fixture，覆盖任务同步、错误状态、图编辑、键盘、便签、持久化、运行控制和 planner 行为。

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/productionCanvas*.test.tsx tests/productionCanvas*.test.ts` -> 154 tests passed.
- `cd ai-pic-frontend && npx tsx --test $(find tests -type f \( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \) ! -name 'toastProvider.test.tsx')` -> 279 tests passed.
- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings and no errors.
- `cd ai-pic-frontend && npm run build` -> passed; `/canvas` generated successfully.
- `pre-commit run --files $(git diff --cached --name-only)` -> passed all scoped hooks, including repository contracts, ledger enforcement, Prettier, and frontend lint.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> passed in a detached temporary worktree created from the staged snapshot; backend and frontend images built locally without push.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas?run_id=48d62cd56e1646c4b3f0c77c1a3cd4a6`.
- Chrome DevTools MCP: retried twice; both attempts failed because `http://127.0.0.1:9222/json/version` returned HTTP 404.
- Fallback: Playwright connected over CDP to an independent system Chrome on `[::1]:9222`; this is fallback browser evidence, not Chrome DevTools MCP verification.
- User path: login -> restore canvas run -> select failed `Task #6272` evidence node -> refresh task status.
- Console: no page console errors or warnings during login and run restore.
- Network: login POST 200; production-canvas run restore GET 200; `GET /api/v1/tasks/6272` returned 200 after refresh.
- Result: task node remained selected, refreshed content stayed visible, and active focus returned to the infinite-canvas surface.
- Screenshot: `artifacts/runs/canvas-existing-wip-20260711T171000Z/task-refresh.png`.

3. Conflict signals and corrections:

- Initial production build failed because `productionCanvasNoteActions.ts` no longer exported `removeManualProductionCanvasNote` while a tracked hook and regression test still imported it.
- Restored the helper and duplicated-note dimensions, then reran the affected tests and production build.
- Initial canvas test run had six failures: three stale transform assertions and three shortcut/focus contract regressions. Updated transform assertions for world-bounds translation, restored modifier guards, limited Cmd+D to manual notes, and aligned the toolbar test with parent-owned focus callbacks.

## Next Steps

- Continue from the executable typed-edge phase in `docs/design/production-canvas.md` after the current worktree is committed.
- Keep the unrelated `toastProvider.test.tsx` timer-hang diagnosis in a separate test-stability commit.

## Linked Commits

- Pending.
