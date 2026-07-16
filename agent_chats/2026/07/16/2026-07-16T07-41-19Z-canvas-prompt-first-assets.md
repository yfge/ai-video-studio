---
id: 2026-07-16T07-41-19Z-canvas-prompt-first-assets
date: "2026-07-16T07:41:19Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - prompt-first
  - asset-selection
  - asset-provisioning
  - domain-hierarchy
related_paths:
  - ai-pic-backend/app/services/production_canvas/asset_prompt_intent.py
  - ai-pic-backend/app/services/production_canvas/asset_provisioning.py
  - ai-pic-backend/app/services/production_canvas/context_resolution.py
  - ai-pic-backend/app/services/production_canvas/runner.py
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasShell.tsx
  - ai-pic-frontend/src/components/features/canvas/productionCanvasHierarchyReveal.ts
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasHierarchyStatus.tsx
  - docs/design/production-canvas.md
  - tasks.md
summary: Make new production canvases prompt-first, reuse or create clearly named IP and Environment assets, and reveal only the resolved hierarchy branch.
---

## User Prompt

无限画布不应该一开始就把所有资产列上，而是根据用户的 prompt 选择或创建相应资产。

## Goals

- 新建画布先呈现生产目标输入，不预取或展示账号下的全部 IP、Environment 和 Story。
- 根据 prompt 保守复用匹配资产；只在名称明确且缺失时创建最小 IP/Environment。
- 保持真实业务 lineage：Environment 必须通过 `VirtualIPEnvironment` 进入 IP 资源池，
  显式冲突 ID 不得被静默修复，Story/Episode 不得从歧义文本自动创建。
- 层级视图只加载本次解析出的精确业务分支。

## Changes

- 后端新增 prompt 资产意图解析和 provision 服务，在显式 Story、Episode、Timeline、
  clip 与 IP/Environment lineage 校验通过后，复用或创建最小资产并持久化真实资源池
  关联。纯 prompt 解析独立为小模块以满足 250 行文件上限；规划结果记录资产是复用
  还是创建。
- 新建 `/canvas` 默认进入执行 prompt；层级 hook 不再首屏获取 IP roots。
- 层级 reveal 改为按 resolved context 精确加载 IP、Environment、Story、Episode、
  Timeline clip 和视频资产，并保留手工展开、竞态取消和稳定实体定位。
- 新增 prompt-first、加载失败和未匹配状态，避免无上下文时出现全量资产或空白画布。
- 更新 Phase 7 设计决策和 `tasks.md`，明确 Phase 5 首屏全量根节点行为已被替代。

## Validation

1. Backend focused

- Command:

  ```bash
  pytest -q tests/unit/test_production_canvas_asset_provisioning.py tests/unit/test_production_canvas_skill_plan.py tests/unit/test_production_canvas_context_resolution.py
  ```

  Result: `16 passed`; `0 failed`.

- 第一轮定向测试暴露 4 个旧产品预期：明确命名的缺失 Environment/IP 仍被视为不应
  创建。测试已按 prompt-first 决策更新，同时保留显式冲突 ID 必须拒绝的回归。

2. Frontend focused

- Command:

  ```bash
  npx tsx --test tests/productionCanvasHierarchy.test.tsx tests/productionCanvasHierarchyReveal.test.tsx tests/productionCanvasHierarchySharedContext.test.tsx tests/productionCanvasViewIsolation.test.tsx
  ```

  Result: `14 passed`; `0 failed`.

3. Final gates

- Combined focused backend coverage for prompt-first assets and the single-video
  compatibility path passed `26` tests.
- Combined focused frontend coverage passed `29` tests.
- `npm run lint` completed with `0` errors and `3` pre-existing warnings;
  `npm run build` passed.
- Full backend completed with `2600 passed` and `88 skipped`. Two failures and
  two errors came from concurrent shared `test.db` disk I/O/readonly contention;
  all four affected Canvas tests passed when rerun serially.
- Full frontend completed with `419 passed`; one hierarchy-reveal test file
  exhausted resources under full-suite process concurrency after 454 seconds.
  The same file passed all `6` tests independently in `0.28` seconds.
- `python scripts/check_repo_docs.py`, repository contract checks for staged,
  unstaged, and untracked paths, and `git diff --check` passed.
- `SKIP=backend-pytest pre-commit run` passed every staged-file hook, including
  formatters, repository contracts, ledger enforcement, and frontend lint. The
  first atomic snapshot skipped only the backend quick hook because pytest also
  discovers the dependent untracked single-video test from the second commit;
  the snapshot's targeted backend tests passed as recorded above.
- Real-browser validation used the Playwright fallback because Chrome DevTools
  was unavailable at `127.0.0.1:9222`. The fresh `/canvas` smoke passed and made
  no initial `/virtual-ips/?limit=100` or `/stories?limit=100` inventory request.

## Next Steps

- Keep provider-backed execution disabled for this UI behavior check unless a
  real generation is explicitly required.
- Investigate the full-suite-only hierarchy reveal resource spike separately;
  focused behavior and browser acceptance are green.

## Linked Commits

- This ledger is committed with the implementation.
