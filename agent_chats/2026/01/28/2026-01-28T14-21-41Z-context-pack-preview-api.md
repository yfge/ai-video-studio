---
id: 2026-01-28T14-21-41Z-context-pack-preview-api
date: "2026-01-28T14:21:41Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, context-pack, api]
related_paths:
  - tasks.md
  - ai-pic-backend/app/api/v1/endpoints/episodes/generation.py
  - ai-pic-backend/app/schemas/context_pack_preview.py
  - ai-pic-backend/app/services/context_pack/story_context_pack_builder.py
  - ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py
summary: "Add a Context Pack preview endpoint for episode generation (with budget/toggles)."
---

## User Prompt

- 按 `tasks.md` 推进 Phase 2：需要提供 Context Pack 的 preview/debug 能力，便于前端预览与排障。

## Goals

- 提供一个只读 API：返回 episode 生成将使用的 Context Pack（不调用模型）。
- 支持预算与开关（是否包含角色卡/最近集摘要/continuity ledger），为后续前端弹窗预览做准备。
- 修复 builder 在 `max_recent_episode_summaries=0` 时的边界行为。

## Changes

- Backend: `ai-pic-backend/app/schemas/context_pack_preview.py`
  - 新增 `EpisodeContextPackPreviewRequest`（继承 `EpisodeGenerationRequest`，追加 budget + include 开关）。
- Backend: `ai-pic-backend/app/api/v1/endpoints/episodes/generation.py`
  - 新增 `POST /episodes/context-pack/preview`：合并 story + marketing overrides，构建并返回 `StoryContextPack`。
- Backend: `ai-pic-backend/app/services/context_pack/story_context_pack_builder.py`
  - 修复 `max_recent_episode_summaries=0` 时不应返回全部 recent episodes 的切片 bug。
- Tests: `ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py`
  - 增加零摘要预算的断言覆盖。
- Docs: `tasks.md`
  - Phase 2「preview/debug API」标记完成。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/context_pack/story_context_pack_builder.py ai-pic-backend/app/schemas/context_pack_preview.py ai-pic-backend/app/api/v1/endpoints/episodes/generation.py ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py tasks.md`
- `./docker/build_prod_images.sh`（buildx build+push；tag 为执行时的 HEAD: `31b6692`）
- 说明：本次仅新增预览接口，尚未接入前端与 episode generation 注入，因此未做 Chrome E2E；在完成注入与 UI 后补端到端验证。

## Next Steps

- Episode 生成 prompt/agent 输入显式注入 context pack，并把 `used_context` 写入 `Task.parameters.agent_run`。
- 前端：生成剧集/再生成弹窗接入 preview API，提供上下文预览与开关。
- 生成/回填 `episode_summary`，用于连续性上下文。

## Linked Commits

- (pending)
