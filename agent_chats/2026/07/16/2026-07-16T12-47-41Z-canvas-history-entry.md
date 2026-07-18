---
id: 2026-07-16T12-47-41Z-canvas-history-entry
date: "2026-07-16T12:47:41Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - history
  - blank-canvas
  - browser-validation
related_paths:
  - ai-pic-frontend/src/app/canvas/page.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasHistory.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasShell.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasController.ts
summary: Make the canvas entry list persisted historical runs and provide a truly blank new-canvas action.
---

## User Prompt

`/goal 画布入口应该可以以列表的形式加载历史画布 同时有新建空白画布的操作`

## Goals

- 让 `/canvas` 无 Run 参数时成为历史画布入口，而不是直接进入内置模板。
- 复用现有 `production_canvas_run` 任务持久化数据加载历史记录。
- 提供明确的“新建空白画布”操作，且新会话不渲染内置模板节点。
- 验证历史 Run 恢复和空白画布在真实浏览器中的可见结果。

## Changes

- 新增历史画布入口组件，分页读取现有文本任务、筛选
  `parameters.kind=production_canvas_run`，按最近更新时间排序并显示标题、Run ID 与节点数。
- `/canvas` 显示历史列表；`/canvas?run_id=...` 恢复历史画布；
  `/canvas?new=1` 打开新建空白画布。
- 为画布控制器增加可注入初始状态，保留原有默认模板行为，同时让空白模式以空节点和空边启动。
- 新增历史列表加载/链接测试，并补充空白画布无模板节点回归测试。

## Validation

1. Frontend checks:

- `npx tsx --test tests/productionCanvasHistory.test.tsx tests/productionCanvasBoard.test.tsx`
  - `15 passed`, `0 failed`.
- `npm run lint`
  - `0 errors`; `3 warnings`，均为现有 ESLint config 与两个 `<img>` warning。
- `npm test`
  - 最终 `433 passed`, `0 failed`.
  - 第一次并行全套运行中，既有持久化测试因自动保存和手动保存时序重叠得到
    `432 passed`, `1 failed`；该测试独立复跑 `9 passed`，随后全套干净复跑通过。
- `npm run build`
  - 沙箱内首次因 Google Fonts 网络访问失败；允许网络后暴露并修复一个新增类型导入，
    最终 Next.js production build 通过，`/canvas` 成功生成。

2. Repository checks:

- `python scripts/check_repo_docs.py`
  - passed.
- `python scripts/check_repo_contracts.py --mode diff <canvas history changed files>`
  - passed.
- `git diff --check -- <canvas history changed files>`
  - passed.

3. Browser validation:

- Environment: `http://localhost:8090`, authenticated operator stack.
- Chrome DevTools at `127.0.0.1:9222` timed out on the first attempt; the required retry on
  fresh port `9333` passed with engine `chrome_devtools_mcp`.
- `/canvas` rendered `55` historical canvases; task list request
  `GET /api/v1/tasks?skip=0&limit=100&task_type=text_generation` returned `200`.
- Opening Run `ac9d718962ed46d684e11e54d9586e31` returned `200` and rendered `13` nodes.
- Clicking “新建空白画布” navigated to `/canvas?new=1` and rendered `0` canvas nodes.
- Console errors: none.
- Evidence:
  - `artifacts/runs/canvas-history-entry-20260716T1245Z-cdp-retry/browser_flow.canvas_smoke.json`
  - `artifacts/runs/canvas-history-entry-20260716T1245Z-cdp-retry/canvas_history_interaction.json`
  - `artifacts/runs/canvas-history-entry-20260716T1245Z-cdp-retry/screenshots/canvas_smoke.png`
  - `artifacts/runs/canvas-history-entry-20260716T1245Z-cdp-retry/screenshots/historical_canvas.png`
  - `artifacts/runs/canvas-history-entry-20260716T1245Z-cdp-retry/screenshots/blank_canvas.png`

4. Commit-time revalidation on 2026-07-18:

- `npm run lint`
  - passed with `0 errors` and the same `3` existing warnings.
- `node --import tsx --test tests/productionCanvasHistory.test.tsx tests/productionCanvasBoard.test.tsx`
  - `10 passed`, `0 failed`.
- `npm test`
  - current branch result: `438 passed`, `9 failed` out of `447`.
  - a clean detached worktree at `37db79b4` reproduced the exact same baseline failures:
    all `5` `ProductionCanvasChatBar` cases and `4` of `10`
    `ProductionCanvasPlanner` cases. The scoped canvas-history tests remain green.
- `npm run build`
  - the sandboxed attempt could not fetch Google Fonts; the network-enabled rerun passed and
    generated `/canvas` successfully.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`
  - both backend and frontend production images built locally; no image was pushed.
- `pre-commit run`
  - passed on the exact staged slice after Prettier formatted the two new TypeScript files.
- `pre-commit run --all-files`
  - intentionally skipped because concurrent unrelated frontend and ledger WIP appeared while
    validating; running all-file formatters could rewrite user-owned files. The staged-only gate,
    repository doc check, diff contract check, lint, scoped tests, build, and Docker build ran.

## Next Steps

- 当前实现一次加载并展示全部历史画布；只有当历史量明显影响首屏性能时，再接入列表分页。
- 当前共享工作区还有大量其他未提交 WIP；提交时只应暂存本条记录列出的前端文件、测试和本 ledger。

## Linked Commits

- This ledger is included in the commit created for this task.
