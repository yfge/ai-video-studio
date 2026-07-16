---
id: 2026-07-15T06-37-15Z-canvas-domain-hierarchy
date: "2026-07-15T06:37:15Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - infinite-canvas
  - domain-hierarchy
  - timeline-lineage
  - browser-evidence
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasCandidateReview.tsx
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasCandidateRequestGuard.ts
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasHierarchyView.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasHierarchyModel.ts
  - ai-pic-frontend/src/components/features/canvas/productionCanvasHierarchyTimeline.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunActions.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasHierarchy.ts
  - ai-pic-frontend/tests/productionCanvasHierarchy.test.tsx
  - ai-pic-frontend/tests/productionCanvasHierarchyModel.test.ts
  - ai-pic-frontend/tests/productionCanvasCandidateIdentity.test.tsx
  - ai-pic-frontend/tests/productionCanvasRunStateIdentity.test.tsx
  - ai-pic-frontend/tests/productionCanvasViewIsolation.test.tsx
  - docs/design/production-canvas.md
  - tasks.md
  - artifacts/runs/canvas-domain-hierarchy-20260715/browser-evidence.json
summary: Add a truthful six-column entity hierarchy to Production Canvas while preserving the executable Run graph and exact Timeline clip-asset lineage.
---

## User Prompt

无限画面的结点应该按 IP、环境、故事、剧集、分镜、视频分层；按照标准开放画布
形式并结合项目现状实现，不确定处通过网络调研核实。

## Goals

- `/canvas` 无 Run ID 时提供可浏览的六列业务实体层级。
- 使用真实 IP、Story、Episode、Timeline clip 和同版本 clip asset，不伪造
  Environment 到 Story 的所有权。
- 保留现有可执行 DAG、Run 持久化和深链语义。
- 提供渐进加载、稳定展开/折叠、语义边、层级大纲和真实浏览器证据。

## Changes

- 增加独立的 `业务层级 / 执行图` 视图切换。无 Run ID 默认打开业务层级；带
  `run_id` 的深链继续打开原执行图。
- 业务层级固定为 `IP / 环境 / 故事 / 剧集 / 分镜 / 视频` 六列。IP 到环境使用
  资源边，IP 到 Story 使用参与边；可选虚线只表达“可用环境”，不声称 Story
  拥有 Environment。
- 初始只加载 IP；展开后依次加载 IP 环境与参与 Story、Story 的 Episode、最新
  Script 对应的最新 Timeline video clips。展开单个分镜时才按相同
  `timeline_id + timeline_version + clip_id` 读取真实 clip assets 和活动任务。
- 视频节点使用真实 media asset 与 lineage link 标识；无同版本资产时显示明确的
  missing/generating 占位，不采用可能回退到旧 Timeline version 的 resolved URL。
- 增加固定列位置、已加载后代计数、展开状态缓存、画布缩放/平移/适配、语义边文字、
  大纲与画布选择同步，以及实体工作区/播放入口。
- 增加 refresh epoch，防止刷新前的异步分支回灌；共享 Story 从大纲分支选择时保留
  该分支 IP，上下文和 Episode workspace 深链携带当前 Script。
- 层级图不进入 `ProductionCanvasState`。业务层级激活时禁用执行图 autosave；切换回
  执行图后恢复。Run 输入草稿不再逐字符改 URL；只有创建、保存或恢复成功后才确认
  Run 并同步 URL，路由回写不会重挂载会话或重复恢复；切换到更新的 Run 时会忽略
  旧保存/恢复请求的迟到响应。Run action、候选审核和候选加载也捕获 Run
  identity/epoch；active Run identity 与路由恢复去重标记相互独立，恢复失败不会错置
  当前 Run。路由或持久化纪元变化后，旧响应不会覆盖新 Run 状态、卡住操作状态或
  污染评审 UI。
- 更新 Phase 5 设计、任务板和浏览器验收记录。

## Validation

1. Automated frontend:

- `cd ai-pic-frontend && npm run test`
  - passed: `348` tests across `83` suites.
- `cd ai-pic-frontend && npm run lint`
  - passed with `0` errors; `3` existing warnings remain outside this change.
- `cd ai-pic-frontend && npm run build`
  - passed; Next.js production build and `/canvas` static route generation completed.

2. Repository checks:

- `python scripts/check_repo_docs.py` - passed.
- `python scripts/check_repo_contracts.py --mode diff <Phase 5 files>` - passed.
- `python scripts/check_repo_contracts.py --mode audit` - passed.
- `git diff --check` - passed.
- Independent read-only code review found no remaining P0, P1, or P2 issues.
- Commit-time gates are recorded in the follow-up hierarchy-closure ledger. The
  repository-wide pre-commit attempt exposed existing whole-repo format and Ruff
  debt; all unrelated rewrites were reverted before this feature was staged.
- `DOCKER_CONFIG=/tmp/codex-docker-config-empty BUILD_PUSH=false
./docker/build_prod_images.sh` passed for both backend and frontend images. The
  images were built locally and were not pushed.

3. Real browser:

- Evidence run: `artifacts/runs/canvas-domain-hierarchy-20260715/`.
- Preferred Chrome DevTools connection failed because
  `http://127.0.0.1:9222/json/version` returned HTTP 404. Validation therefore used
  Playwright fallback and is recorded as `degraded`, not Chrome verification.
- Live path passed: IP `84` -> Story `61` -> Episode `174` -> Timeline `70` v6 ->
  stable clip `video_scene_584_beat_4176_001` -> current-version asset node
  `video:885`.
- IP roots, environments, stories, episodes, scripts, timelines, clip tasks,
  exact-version clip assets, and saved Run `9a4bbfdb95f846e4be216beb1b09ad88`
  all returned HTTP 200.
- Verified six columns, solid/dashed/production relations, outline focus, collapse
  and reopen without refetch or position change, view-state preservation, Run deep
  link routing, Run draft URL isolation, and read-only Run requests. Browser console
  errors: `0`.

## Next Steps

- Current APIs cap IP and Story discovery at 100 records. The UI warns when the cap
  is reached; accounts above it need server-side cursor/filter support.
- Repair the local Chrome DevTools endpoint if future delivery requires a non-degraded
  Chrome evidence run. The Playwright fallback already proves the current user path.

## Linked Commits

- Included in the current Canvas hierarchy closure commit.
