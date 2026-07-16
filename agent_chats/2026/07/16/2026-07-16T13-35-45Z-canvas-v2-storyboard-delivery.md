---
id: 2026-07-16T13-35-45Z-canvas-v2-storyboard-delivery
date: "2026-07-16T13:35:45Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - clip-storyboard
  - browser-validation
  - delivery
related_paths:
  - docs/design/production-canvas.md
  - tasks.md
summary: Record the canonical clip-storyboard v2 design, deterministic browser evidence, completed atomic commits, and remaining provider-backed acceptance gap.
---

## User Prompt

采用故事板的形式，不用首尾帧了。按确认方案实现，并保持最小化颗粒度提交。

## Goals

- 将 Production Canvas 的设计与任务真源更新为 canonical clip-storyboard v2。
- 记录后端、前端和真实浏览器验证证据，区分确定性非付费验证与 provider-backed
  发布验收。
- 保留旧 v1 Run 的首帧语义，但不让它出现在新建 v2 画布。

## Changes

- 设计文档明确十一个规范 Skill、十一条 typed edges、clip-scoped 2/4/6/9 格
  故事板、整张故事板视频参考和显式 `timeline.place`。
- `tasks.md` 将已完成的 v2 结构/交互浏览器证据与仍待完成的 provider-backed
  视频生成和 Timeline lineage 验收拆开记录。
- 浏览器证据记录为 Playwright fallback；没有把 Chrome DevTools 超时或被拦截的
  付费生成请求描述成真实 provider 验收。

## Validation

- Post-rebase backend focused suites:
  - planner and execution contracts: `23 passed`.
  - v1/v2 video port compatibility: `12 passed`.
- `cd ai-pic-backend && pytest`
  - `2633 passed`, `96 skipped`, `1 failed`.
  - the remaining
    `tests/integration/test_single_video_project_api.py::test_single_video_canvas_plan_reuses_unique_prompt_asset`
    failure reproduces unchanged on `main` at `cc0a693a` and is not introduced by
    this delivery.
- Post-rebase frontend focused suites:
  - storyboard/graph/interaction contracts: `75 passed`; `0 failed`.
  - `productionCanvasPorts.test.ts`: `4 passed`; `0 failed`.
- `cd ai-pic-frontend && npm test`
  - `429 passed`, `9 failed`; all 9 failures reproduce unchanged on `main` at
    `cc0a693a` in `ProductionCanvasChatBar` and `ProductionCanvasPlanner` tests.
- `cd ai-pic-frontend && npm run lint`
  - `0 errors`; 3 pre-existing warnings.
- Chrome browser evidence after fast-forwarding to `main`:
  `artifacts/runs/canvas-storyboard-v2-merge-20260717/browser-validation.json`
  - `result=passed`, preferred engine `chrome-extension`; an independent Codex
    in-app browser pass produced the same assertions.
  - the Video Candidates node accepts `选用故事板 image`; no start-frame or
    end-frame port is present.
  - the whole-storyboard guidance and explicit `Timeline Place` node are visible.
  - no browser console warning/error; `/canvas` and local login requests completed
    with HTTP 200 in Nginx/backend logs.
- Earlier deterministic pre-Phase-9 evidence remains at
  `artifacts/runs/canvas-v2-storyboard-20260716T1320Z/canvas_storyboard_e2e.json`.
- `python scripts/check_repo_docs.py`
  - passed.
- `python scripts/check_repo_contracts.py --mode diff <changed paths>`
  - passed.
- Pre-commit changed-file checks
  - passed.
- `env BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`
  - no image was pushed; the local legacy builder stalled while sending the build
    context, so the production-image build gate remains incomplete.

## Next Steps

- 在当前环境运行一次 provider-backed v2 全链：真实故事板生成和选用、整张故事板
  视频请求、视频选用、显式 Timeline 放置及最终资产 lineage 断言。
- 修复上述仓库基线测试失败，并完成一次不受本地 legacy builder 阻塞的生产镜像构建。

## Linked Commits

- `4a9cee04` `feat(canvas): add clip storyboard candidate flow`
- `465b4ff5` `feat(canvas): switch planner to clip storyboard flow`
- `74d7a8a4` `feat(canvas): align frontend with clip storyboard flow`
- `7969d629` `fix(canvas): version video ports for storyboard plans`
- `87920ab5` `fix(canvas): deduplicate planned edges on refresh`
- This ledger is included in the design and task-board delivery commit created for this task.
