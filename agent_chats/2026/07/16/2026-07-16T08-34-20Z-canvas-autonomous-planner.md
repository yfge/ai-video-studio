---
id: 2026-07-16T08-34-20Z-canvas-autonomous-planner
date: "2026-07-16T08:34:20Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - autonomous-planner
  - typed-dag
  - reliability
  - browser-validation
related_paths:
  - ai-pic-backend/app/services/production_canvas/autonomous_planner.py
  - ai-pic-backend/app/services/production_canvas/planner_contracts.py
  - ai-pic-backend/app/services/production_canvas/planner_ports.py
  - ai-pic-backend/app/services/production_canvas/skill_planner.py
  - ai-pic-frontend/src/components/features/canvas/productionCanvasPlanGraph.ts
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasDefinitionActions.ts
  - docs/design/production-canvas.md
  - tasks.md
summary: Add a bounded autonomous planner that proposes a minimal skill subset, compiles it into an allowlisted typed DAG, and falls back deterministically with evidence.
---

## User Prompt

实现无限画布下 Agent 的自主 Planner 能力；查询最新论文和研究，保证 Planner 管线可靠、
可行，并提交改动。

## Goals

- 根据生产目标与已解析业务上下文，自主选择最小可行 Skill 子集和依赖。
- 保持模型与执行器隔离，由确定性后端编译器验证类型化 DAG 后才允许进入 Run。
- 对 provider、结构化输出和图可行性失败提供有界修复与确定性回退证据。
- 让前端创建和恢复都消费服务端返回的动态节点与边。

## Changes

- 新增结构化 Planner prompt、schema 和 evidence；LLM 只提议 Skill 与依赖，不直接调用
  worker。
- 新增白名单 Skill/port contract 编译器，校验未知 Skill、缺失前置、非法依赖、重复绑定、
  类型不兼容和环路，并复用 Graph v2 saved-state 校验作为最终可行性门。
- 结构化输出最多修复一次；provider 或编译失败时返回确定性完整方案，并记录 mode、
  provider/model、修复次数、校验错误与 fallback reason。
- Plan/Run 响应携带显式端口、动态边与 Planner evidence；Run 恢复保留所选 Skill 子集，
  不再重新扩成固定完整链路。
- 前端使用服务端动态边创建与恢复执行图，并以 transient planned edge 避免污染持久化
  node contract。
- 更新设计文档和 Phase 8 任务状态，记录 planner/compiler/executor 边界及研究依据。

## Validation

1. Backend focused

- `pytest -q tests/unit/test_production_canvas_autonomous_planner.py
tests/unit/test_production_canvas_graph_validation.py
tests/unit/test_production_canvas_graph_runtime.py`
  - `22 passed`; `0 failed`.
- Skill/context/API 扩展组合最初得到 `20 passed, 2 errors`；两个错误均来自并行测试共享
  SQLite 文件导致的 `attempt to write a readonly database`，不是 Planner 断言失败。
- 两个受影响 context case 随后分别在独立临时目录运行，均为 `1 passed`。
- `AI_FORCE_MOCK=true` 的 Plan API 集成 case 在独立临时目录运行，`1 passed`。

2. Frontend focused

- `npx tsx --test tests/productionCanvasPlanGraph.test.ts
tests/productionCanvasSkillNodes.test.ts
tests/productionCanvasServerRestore.test.ts
tests/productionCanvasPersistence.test.tsx
tests/productionCanvasExecutionResults.test.ts
tests/productionCanvasSkillPlannerRunId.test.tsx`
  - `33 passed`; `0 failed`.
- `npm run lint`
  - `0 errors`; `3 warnings`，均为现有 ESLint config / `<img>` warning。
- 全量 frontend suite 已运行并通过多组 suite，但在并行工作区正在修改的
  `productionCanvasHierarchyReveal.test.tsx` 停滞后主动中止；未宣称全量通过。

3. Browser evidence

- Chrome DevTools transport 在当前环境超时；按仓库策略明确降级为 Playwright。
- `artifacts/runs/canvas-autonomous-planner-20260716T1630/browser_flow.json`
  记录通用 `canvas_smoke` 通过。
- 定制浏览器路径使用 stubbed Plan 响应、禁用付费 provider 调用，验证画布只渲染
  `brief -> script` 两个 Planner 节点与动态边；POST `/plan` 为 `200`，console errors
  为空。
- Evidence:
  `artifacts/runs/canvas-autonomous-planner-20260716T1630/planner_browser_evidence.json`
  与
  `artifacts/runs/canvas-autonomous-planner-20260716T1630/screenshots/autonomous-planner-subset.png`。
- 后端真实 Planner 编译路径由 unit/API 测试独立覆盖；本次浏览器验证不产生模型或生成费用。

4. Commit gates

- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <staged files>`: passed.
- Staged-slice pre-commit hooks passed after applying the hook's isort/prettier
  output. `pre-commit run --all-files` remains blocked by repository-wide
  pre-existing formatting drift and 69 unrelated Ruff findings, so no unrelated
  hook rewrites were copied back.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64
./docker/build_prod_images.sh` kept remote push disabled, but the legacy
  builder stalled while sending the local context. A local buildx `--load`
  retry then stalled at Docker Hub metadata lookup for `python:3.11-slim` and
  was cancelled. No image was pushed; production image build remains an
  environment validation gap.

## Next Steps

- Docker Hub/build-builder connectivity 恢复后，重跑本地 non-pushing production
  image build。
- 后续如需更强自适应，可在 Run 状态机上增加有预算、可审计的执行期重规划；本次保持
  单次提议、一次修复和确定性回退。

## Linked Commits

- This ledger is included in the commit created for this task.
