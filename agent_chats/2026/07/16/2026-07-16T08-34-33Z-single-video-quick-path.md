---
id: 2026-07-16T08-34-33Z-single-video-quick-path
date: "2026-07-16T08:34:33Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - single-video
  - production-canvas
  - story-workspace
  - timeline
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/stories/single_video.py
  - ai-pic-backend/app/services/single_video_project_service.py
  - ai-pic-frontend/src/components/features/stories/SingleVideoProjectModal.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasChatBar.tsx
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - docs/design/production-canvas.md
  - tasks.md
summary: Add a shared 3- or 5-minute single-video quick path to the project list and Production Canvas while keeping Story and Episode as hidden compatibility records.
---

## User Prompt

现在故事-剧集-剧本是不是太重了，如果用户想直接创建一个三分钟五分钟的视频就不适用。
同时在无限画布上也要引入这个能力。

## Goals

- 让用户无需先设计系列 Story/Episode，就能创建一条 3 或 5 分钟视频。
- 普通项目入口和 Production Canvas 复用同一后端创建能力。
- 保留现有 Script、Timeline、Task 和媒体生产链，不另造一套生成系统。
- 不因快捷创建自动触发图片、视频、渲染或导出费用。

## Changes

- 新增 `POST /api/v1/stories/single-video`，创建带
  `creation_mode=single_video` 的系统管理 Story/Episode；IP 和 Environment 可选，
  同时校验资产所有权与真实资源池关系。
- `/stories` 增加“创建单条视频”入口，支持 3/5 分钟、9:16/16:9 和可选风格；
  创建后直接进入 Script 工作区并跟踪现有剧本生成 Task。
- `/canvas` 增加“单条视频 / 系列制作”模式。单条视频模式先创建兼容项目，再生成
  Canvas 计划，并只自动执行 `script.generate`。
- 无 IP 时，业务层级以真实视频项目 Story 为根并显示
  `视频项目 -> 主视频`；没有伪造 IP 或 Environment 父节点。
- `planning_mode=single_video` 写入计划节点并贯穿浏览器和服务端执行请求，防止 Run
  恢复或手动执行时重新按 prompt 猜测资产。

## Validation

- Backend focused:
  `pytest -q tests/integration/test_single_video_project_api.py
tests/unit/test_production_canvas_context_resolution.py
tests/unit/test_production_canvas_skill_plan.py
tests/unit/test_production_canvas_asset_provisioning.py
tests/unit/test_production_canvas_run_persistence.py
tests/unit/test_production_canvas_single_video_run_request.py`
  -> `26 passed`.
- Frontend focused:
  `npx tsx --test tests/singleVideoProjectEntry.test.tsx
tests/singleVideoCanvasPlanner.test.tsx tests/singleVideoWorkspace.test.tsx
tests/productionCanvasChatBar.test.tsx
tests/productionCanvasHierarchyModel.test.ts
tests/productionCanvasHierarchyReveal.test.tsx
tests/productionCanvasSkillRequest.test.ts
tests/episodeScriptTaskTracking.test.ts`
  -> `29 passed`.
- `npm run lint` -> 0 errors and 3 pre-existing warnings.
- `npm run build` -> passed after allowing the build to fetch Google Geist
  fonts.
- Full backend -> `2600 passed`, `88 skipped`; 2 failures and 2 errors came
  from concurrent shared `test.db` disk I/O/readonly contention. The four
  affected Canvas tests passed when rerun serially.
- Full frontend -> `419 passed`, one file-level failure:
  `productionCanvasHierarchyReveal.test.tsx` consumed high CPU under full-suite
  process concurrency and exited after 454 seconds. The same file passed all
  6 tests in the focused run in 0.28 seconds, including the new no-IP
  single-video reveal assertion.
- `python scripts/check_repo_docs.py`, repository contract diff checks for
  staged, unstaged, and untracked files, and `git diff --check` all passed.
- Browser validation used Playwright fallback because Chrome DevTools could not
  open `http://127.0.0.1:9222`. Standard `/canvas` smoke passed. The interaction
  run at `artifacts/runs/single-video-quick-path-20260716/` used intercepted
  generation responses to avoid provider cost and database pollution, then
  asserted:
  - `/stories` submitted a 5-minute 16:9 project with
    `start_generation=true` and no IP requirement.
  - `/canvas` submitted `start_generation=false`, planned with
    `planning_mode=single_video`, then made exactly one Execute request for
    `script.generate`.
  - No automatic image, video, render, or export request was issued.
  - The interaction console contained no errors.

## Next Steps

- Optional harness cleanup: update the existing
  `story_master_detail_smoke.required_text` from the retired “故事列表” copy to
  the current “故事入口” or add a dedicated single-video scenario.
- Investigate the full-suite-only resource spike in
  `productionCanvasHierarchyReveal.test.tsx`; functional assertions are green
  when the file is run independently.

## Linked Commits

- `fc30ae44` — prompt-first Canvas asset resolution required by this flow.
- This ledger is committed with the implementation.
