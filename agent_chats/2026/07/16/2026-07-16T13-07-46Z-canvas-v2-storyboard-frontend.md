---
id: 2026-07-16T13-07-46Z-canvas-v2-storyboard-frontend
date: "2026-07-16T13:07:46Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - frontend
  - clip-storyboard
  - timeline-placement
related_paths:
  - ai-pic-frontend/src/components/features/canvas/productionCanvasDefaultGraph.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPlanGraph.ts
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasCandidateReview.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasMediaControls.tsx
summary: Align the Production Canvas frontend with the canonical clip-storyboard flow and explicit Timeline placement.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 让新建 Production Canvas 只展示 clip storyboard sheet 驱动的视频链路。
- 故事板格数按片段时长自动选择 2 / 4 / 6 / 9 格，不暴露首尾帧参数。
- 故事板和视频候选保持 clip scope，并保留人工选用证据。
- 新链路由独立 `timeline.place` 节点回填视频，候选卡不再直接写 Timeline。
- 继续恢复旧 v1 画布，但不让旧首帧 binding 出现在新规范图中。

## Changes

- 将前端默认图切换为 Brief、Assets、Script、Timeline、Storyboard Candidates、
  Video Candidates、Timeline Place、Render、Export、Report 十个规范节点及十一条
  typed edges。
- 新规范图使用 `approved_storyboard -> approved_storyboard`，不包含
  `start_frame` 或尾帧 binding。
- 为 clip storyboard 增加候选审核、协作候选加载和自动 2 / 4 / 6 / 9 格提示，
  同时隐藏帧索引、视频时长、宽高比等不适用参数。
- 对故事板候选和 clip-storyboard 视频关闭候选分支；显式放置模式下隐藏候选卡的
  “放入 Timeline”捷径，由 `timeline.place` 节点负责回填。
- 新增 `timeline_clip`、`approved_storyboard`、`placed_timeline` 和 `delivery`
  端口，并为客户端计划图保留 v1 恢复分支。
- 将默认图从 `productionCanvasModel.ts` 拆出，并把 Board 交互测试按完整测试函数
  拆分，确保本次新增和拆分文件不超过 250 行。
- 更新旧默认图测试断言，验证故事板到视频的 selected-output binding，且新图不存在
  `start_frame` 输入。

## Validation

- `cd ai-pic-frontend && npm run lint`
  - `0 errors`; 仅保留仓库已有的 3 个 warning。
- `cd ai-pic-frontend && npm test`
  - `432 passed`; `0 failed`.
- Storyboard/graph focused tests:
  `node --import tsx --test tests/productionCanvasGraph.test.tsx tests/productionCanvasKeyboard.test.tsx tests/productionCanvasPersistence.test.tsx`
  - `47 passed`; `0 failed`.
- `python scripts/check_repo_contracts.py --mode diff <changed frontend paths>`
  - passed.
- `git diff --check`
  - passed.
- Changed-file line counts:
  - all new or split frontend source and test files are at or below 250 lines.
- Production build:
  - the default Turbopack command could not follow the temporary worktree's external
    `node_modules` symlink.
  - `npx next build --webpack` completed successfully after allowing the existing
    Google Fonts download.

## Next Steps

- 更新设计文档和 `tasks.md` 中仍指向关键帧/首帧的视频链路说明。
- 在真实浏览器验证新建画布、故事板候选审核和显式 Timeline 放置路径。
- 将隔离工作树中的 Planner、Frontend 和文档原子提交安全整合回主工作树。

## Linked Commits

- This ledger is included in the frontend clip-storyboard commit created for this task.
