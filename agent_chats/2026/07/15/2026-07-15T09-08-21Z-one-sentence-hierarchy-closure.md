---
id: 2026-07-15T09-08-21Z-one-sentence-hierarchy-closure
date: "2026-07-15T09:08:21Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - one-sentence-generation
  - domain-hierarchy
  - run-context
  - browser-evidence
related_paths:
  - ai-pic-backend/app/services/production_canvas/run_context.py
  - ai-pic-backend/app/services/production_canvas/run_persistence.py
  - ai-pic-backend/app/services/task_result_context.py
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasHierarchyView.tsx
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasTaskSync.ts
  - docs/design/production-canvas.md
  - tasks.md
summary: Close one-sentence generation over the truthful IP, Environment, Story, Episode, Storyboard, and Video hierarchy.
---

## User Prompt

无限画面的结点应该按 `IP / 环境 / 故事 / 剧集 / 分镜 / 视频` 分层走下去；
确认它与之前的一句话动态生成相吻合，并完成该需求。

## Goals

- 让业务层级与一句话生成共享同一套真实领域标识和 lineage，而不是维护两套图。
- 一句话生成后自动延续现有执行链，并把 Script、Timeline、clip、Task 和视频结果
  回写到当前 Run 与业务层级。
- 保持 Environment 为 IP 可复用资源，Storyboard 为 Timeline clip，Video 为同版本
  clip asset；不伪造业务所有权。
- 阻止跨 Run、同 Run 已换 Task、旧上下文指纹和旧层级 reveal 的迟到响应污染当前分支。

## Changes

- 后端新增并贯通 typed `resolved_context` / `result_context`：Plan、Execute、Run saved
  state、Task、Script agent run、Timeline placement 和 Render 共用
  `virtual_ip_id / environment_id / story_id / episode_id / script_id /
timeline_id / timeline_version / clip_id / task_id`。
- 一句话规划优先校验显式 ID 与 lineage，再保守匹配可访问 Story 和明确的第 N 集；
  歧义时保持 blocked，不隐式创建 Story/Episode。Run 持久化使用上下文 revision，避免
  首次保存和执行回写互相覆盖。
- 前端把一句话自动执行、Task/Render 跟踪、Run 恢复、候选放置和六列业务层级连成
  闭环。生成结果按 revision 自动展开到最深真实实体；手工层级选择会取消旧 reveal，
  并反向写回下一次规划上下文。
- 图片/视频候选继续按 Script + Timeline + stable clip 隔离；参考图必须匹配当前 IP /
  Environment，审核和 Timeline 放置仍是显式操作。
- Task cancelled/failed/timeout、Render timeout、上下文指纹过期和同 Run Task 替换均
  收敛为 terminal/stale 状态，不再把节点永久留在 running，也不会发布旧领域上下文。
- Task agent-run 的领域引用改用现有 Repository，移除本次触达文件中的直接 ORM
  查询；新增代码保持在仓库文件大小门禁内。
- 更新 `docs/design/production-canvas.md` Phase 6 与 `tasks.md` 完成状态。

## Validation

1. Backend

- `cd ai-pic-backend && pytest`
  - passed: `2594`; skipped: `88`; failed: `0`; warnings: `3880`.
- Repository 收敛后的定向回归：`26 passed`，覆盖 agent-run 持久化、Task result
  context 和一句话上下文解析。
- 独立最终审查确认 Task complete → autosave → reload 的 revision/CAS 路径已闭环；
  复核定向测试为 backend `19 passed`、frontend `24 passed`，无剩余 P0–P2。
- `ruff check` 覆盖本次 backend 服务、schema、repository 与测试：通过。

2. Frontend

- `cd ai-pic-frontend && npm run test`
  - passed: `411` tests across `91` suites; failed: `0`.
- 新增竞态定向回归：同 Run 旧 Task、上下文 fingerprint、Task cancel/timeout、Render
  timeout、跨 IP reference artifact、手工层级选择与旧 reveal；全部通过。
- `npm run lint`：`0` errors；保留 `3` 个与本次无关的既有 warnings。
- `npm run build`：通过；Next.js production build 和 `/canvas` route 生成成功。

3. Repository contracts

- `python scripts/check_repo_docs.py`：通过。
- `python scripts/check_repo_contracts.py --mode audit`：通过。
- `python scripts/check_repo_contracts.py --mode diff <changed files>`：通过。
- `git diff --check`：通过。
- `pre-commit run --all-files`：已执行；全仓模式被既有 69 个 Ruff 错误和历史文件格式
  漂移阻断，并机械改写了 244 个本需求之外的文件。所有这些无关改写均已精确撤回。
- `pre-commit run`（仅 staged feature files）：通过；backend quick gate 与 frontend
  lint 均通过。格式化后出现的两个 250 行门禁通过最小测试拆分和空行压缩解决。
- `pytest tests/integration/test_production_canvas_timeline_placement_api.py
tests/integration/test_production_canvas_timeline_placement_version_api.py -v`：`2 passed`。
- `DOCKER_CONFIG=/tmp/codex-docker-config-empty BUILD_PUSH=false
./docker/build_prod_images.sh`：通过；后端、前端镜像仅在本机生成，未推送 registry。

4. Real browser

- 一句话闭环证据：`artifacts/runs/canvas-one-sentence-hierarchy-closure-20260715/`。
  真实 Plan 解析到 Story `61` / Episode `174`；后续请求携带 Script `144`、Timeline
  `70` v6、clip `video_scene_584_beat_4176_001`，层级定位视频 asset `353`；Task
  `6357` 返回相同九字段上下文。provider execute 使用显式 stub，未产生付费生成。
- 最终 smoke：`artifacts/runs/canvas-one-sentence-hierarchy-closure-final3-20260715/`。
  `/canvas` 显示全部六列，IP roots HTTP 200，console errors `0`，截图视觉检查通过。
- Chrome DevTools 在 `http://127.0.0.1:9222` 等待超时；按策略使用 Playwright
  fallback，证据状态为 `degraded`，未声明 Chrome 验证。

## Next Steps

- 如交付要求非降级 Chrome 证据，需要先修复本机 Chrome DevTools 9222 transport。
- IP/Story 查询当前最多展示 100 项；超过该规模时应补服务端 cursor/filter。

## Linked Commits

- Included in the current Canvas hierarchy closure commit.
