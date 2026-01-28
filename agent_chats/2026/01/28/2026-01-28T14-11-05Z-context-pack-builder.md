---
id: 2026-01-28T14-11-05Z-context-pack-builder
date: "2026-01-28T14:11:05Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, context-pack]
related_paths:
  - tasks.md
  - ai-pic-backend/app/schemas/context_pack.py
  - ai-pic-backend/app/services/context_pack/__init__.py
  - ai-pic-backend/app/services/context_pack/budgeting.py
  - ai-pic-backend/app/services/context_pack/story_context_pack_builder.py
  - ai-pic-backend/app/services/context_pack/episode_context_pack_builder.py
  - ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py
summary: "Define Context Pack schemas and add a budget-aware builder with unit tests."
---

## User Prompt

- 按 `tasks.md` 推进故事/剧集生成质量闭环（Phase 2：Context Pack），补上下文管理与一致性能力。

## Goals

- 定义 `StoryContextPack` / `EpisodeContextPack` 字段与预算结构，作为 episode 生成统一上下文入口。
- 实现 context pack builder：从 DB + story snapshot 组装，并支持按预算裁剪（先用字符预算避免 token 依赖）。
- 补单测，确保字段稳定与裁剪策略可预期。

## Changes

- Backend: `ai-pic-backend/app/schemas/context_pack.py`
  - 新增 Context Pack schemas（预算、meta、角色卡、世界观/大纲核心、最近 N 集摘要等）。
- Backend: `ai-pic-backend/app/services/context_pack/`
  - `budgeting.py`：基础裁剪工具（truncate + best-effort shrink 策略）。
  - `story_context_pack_builder.py`：Story 级 context pack 组装（角色/最近摘要/风格与禁区偏好）并应用预算裁剪。
  - `episode_context_pack_builder.py`：Episode 级包装（复用 story pack + episode_number）。
- Tests: `ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py`
  - 覆盖 builder 的组装与紧预算裁剪行为（如 biography 被裁剪/保留最近摘要等）。
- Docs: `tasks.md`
  - Phase 2 任务拆分更细，并标记 schema + builder 已完成。

## Validation

- `pre-commit run --files ai-pic-backend/app/schemas/context_pack.py ai-pic-backend/app/services/context_pack/__init__.py ai-pic-backend/app/services/context_pack/budgeting.py ai-pic-backend/app/services/context_pack/story_context_pack_builder.py ai-pic-backend/app/services/context_pack/episode_context_pack_builder.py ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py tasks.md`
- `./docker/build_prod_images.sh`（buildx build+push；tag 为执行时的 HEAD: `6000094`）
- 说明：本次变更尚未注入 episode 生成链路/暴露 preview 接口，因此暂未进行 Chrome E2E；会在注入完成后补端到端验证与抽检。

## Next Steps

- 新增 context pack preview/debug API（用于前端预览与排障）。
- Episode 生成 prompt/agent 输入显式注入 context pack，并把 `used_context` 写入 `Task.parameters.agent_run`。
- 生成/回填每集摘要 `episode_summary`，用于后续连续性。

## Linked Commits

- (pending)
