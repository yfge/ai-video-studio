---
id: 2026-07-22T18-00-04Z-narrative-memory-v1
date: "2026-07-22T18:00:04Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - narrative-memory
  - story-seed
  - dramatic-state
  - character-growth
related_paths:
  - docs/design/narrative-memory-and-dramatic-state.md
  - ai-pic-backend/app/services/narrative_memory
  - ai-pic-frontend/src/components/features/story-memory
summary: Implement story-scoped long-term narrative memory, anchored character growth, manual shared-memory promotion, and operator UI.
---

# Narrative memory v1 implementation

## User Prompt

实现完整设计：长篇故事需要 Story 范围的长期叙事记忆、每个角色独立的成长记忆、带
发生/获知/生效锚点的稳定召回、经人工处理的角色公共记忆，并区分潜台词、离场已发生
事件和观众显隐；同时更新 Story、Novel、Episode、Script 与 Virtual IP 的 UI。

## Goals

- 把新系列的 Story 入口缩减为结构化、可编辑的 `story_seed_v1`，不再复制下游生产规划。
- 落地 Story 私有事件、角色记忆、成长 snapshot、锚点、来源版本和 stale 传播。
- 保证 Story 与 canon branch 隔离，公共记忆只能人工提炼、审批并冻结到 Story 基线。
- 在 Episode/Script 生成中冻结可追溯的记忆证据，区分离场事件、观众显隐和潜台词。
- 提供审核、基线同步、公共记忆和 Dramatic State 的 API 与 Operator UI。

## Changes

- 新增两组 Alembic 迁移和 Narrative Anchor/Event、Character Memory/Snapshot/Promotion
  模型、schema、repository、service 与 API；角色私有记忆强制发生、获知和生效锚点。
- Story 生产生成改用 `StorySeedEnvelope`、严格解析和最多一次 repair；Story Seed 保存、
  确认及编辑会更新 review/stale 状态，但不自动重写下游。
- Novel 章节按章节起点读取记忆；Episode、Script 和 Task agent run 保存 snapshot、ledger、
  source hash 与 disclosure 证据；来源或公共基线变化确定性标记 stale。
- 公共记忆通过人工 promotion、审批、clone/supersede 发布，并按 Virtual IP 与
  `canon_branch_id` 隔离；在制 Story 默认保持冻结版本，手工同步才更新。
- 新增 Story Seed 编辑/确认、叙事记忆健康和独立四-tab 工作区；Novel 章节提取状态、
  Episode 记忆证据、Virtual IP 公共记忆工作区及 Script 场景潜台词 Inspector。
- 更新叙事记忆、生成质量和 Story→Novel→Episode→Script 设计文档，记录 v1 实施状态。
- 未修改或纳入交付已有的音频尾部补帧 WIP、其测试/ledger，以及 `outputs/` 文件。

## Validation

- `pytest -q tests/unit tests/test_models.py tests/test_migration_simple.py tests/test_migrations.py`
  → `2214 passed, 59 skipped`。
- Narrative memory/Story Seed 焦点集合 → `17 passed`；覆盖 Story 隔离、时间锚点、稳定
  snapshot、来源失效、人工 promotion、分支隔离、offscreen disclosure、潜台词 gate 和
  Story Seed 下游失效。
- `npm run lint` → 0 error，3 个仓库既有 warning。
- `npx tsx --test tests/storyOutlineSection.test.tsx` 和
  `npx tsx --test tests/storyNovelWorkflowPanel.test.tsx` → 各 `2 passed`。
- `npm run test` → 453 tests 中 444 passed、9 failed；失败全部位于既有
  `ProductionCanvasChatBar`/`ProductionCanvasPlanner` 基线，与本变更路径无关。
- `npm run build` → production build 通过；包含 `/stories/[id]/memory` 和
  `/virtual-ip/[id]/memories`。首次 sandbox 构建仅因 Google Fonts 网络被阻断，授权联网后
  通过。
- `python scripts/check_repo_docs.py`、`python scripts/check_repo_contracts.py --mode audit`、
  面向本 changeset 的 `check_repo_contracts.py --mode diff`、`python -m compileall -q app`、
  `alembic heads`、`git diff --check` 全部通过；Alembic head 为 `a8b9c0d1e2f3`，本地
  Docker 开发库已升级到该版本。
- 针对本变更文件运行 ruff、black、isort 和 prettier，复跑全部通过。工作区存在用户 WIP，
  因此未运行可能改写无关文件的 `pre-commit run --all-files`。
- `BUILD_PUSH=false ./docker/build_prod_images.sh` → 后端、前端 production image 均在本地
  构建成功；显式关闭 registry push。
- 浏览器 run：`artifacts/runs/narrative-memory-v1-20260723/summary.json`。Chrome DevTools
  `127.0.0.1:9222/json/version` 返回 HTTP Not Found；Playwright/system Chrome 启动未完成，
  installed Chromium 后续启动不稳定；最终按 fallback 规则使用 Selenium/Safari 完成登录、
  Story Seed 本地创建、Story 详情/记忆工作区、Virtual IP 公共记忆和 Script Dramatic State
  的真实导航与 DOM 断言。Safari WebDriver PNG 在本机为全黑，已明确标记为不可用截图，
  不作为可见 UI 证明。
- 浏览器验收只创建草稿 `记忆机制验收-20260723-safari`
  (`99b1a35929dc4bb0981e49b3eb2018ee`)；未启动任何付费生成、提取、检查或建议调用。

## Next Steps

- `ProductionCanvasChatBar` 5 个测试与 `ProductionCanvasPlanner` 4 个测试是独立基线债务，
  应在其自身任务中处理。

## Linked Commits

- Design baseline: `60fc8779 docs(design): define narrative memory architecture`
- Implementation: this commit
