---
id: 2026-01-28T13-03-27Z-episode-generation-strict-persistence
date: "2026-01-28T13:03:27Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, episodes, structured-output, agent-run, validation]
related_paths:
  - ai-pic-backend/app/services/ai/episodes.py
  - ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py
  - ai-pic-backend/app/services/episode/episode_generation_service.py
  - ai-pic-backend/app/services/episode/episode_generation_utils.py
  - ai-pic-backend/tests/unit/services/ai/test_episode_generation_strict.py
  - ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py
  - tasks.md
summary: "Make episode generation fail-fast: strict EpisodePlan validation/repair, no coercive fallback writes, and richer agent_run audit (raw/normalized/errors/repairs)."
---

## User Prompt

- 故事/剧集生成逻辑需要更严格：有上下文/校验/验正；按 `tasks.md` 推进 Phase 1，原子化提交并更新文档。
- 在 docker 容器里自测，并用 Chrome 走 E2E（含失败 case）。

## Goals

- Episode plan：`episodes` 数量必须严格等于 `episode_count`，字段/内容最小约束不满足则触发 repair；最终失败不落库 Episode。
- 任务审计：把 raw content、normalized、校验错误与 repair 过程写入 `Task.parameters.agent_run`，便于复现/排障。
- 落库一致性：任务最终失败时，不留下半成品 Episode（软删本次创建的记录）。

## Changes

- Backend: `ai-pic-backend/app/services/ai/episodes.py`
  - 通过 `generate_with_repair(...)` + `extra_validator` 强制 episodes 数量 == `episode_count`，并在 schema 上设置 `minItems/maxItems` hint。
  - 统一返回 `normalized/validation_errors/repair_attempts/first_attempt`，并在成功后写入 continuity postprocess 结果。
- Backend: `ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py`
  - 移除 `_coerce_episode_payload` 这类“兜底写入”路径：Episode 回调落库前必须通过 `EpisodePlanItem` schema + `is_episode_payload_valid`。
  - `Task.parameters.agent_run` 追加 `raw_content/normalized/react_attempts/duration_accepted/continuity_snapshot` 等审计字段。
  - 任务完成前校验是否具备 `1..episode_count` 的所有集；失败时软删本次创建的 Episode。
- Backend: `ai-pic-backend/app/services/episode/episode_generation_utils.py`
  - 新增 `build_agent_run_info(...)`，抽取 result→agent_run 的通用映射，避免 service 文件膨胀。
- Backend: `ai-pic-backend/app/services/episode/episode_generation_service.py`
  - 使用 `build_agent_run_info(...)`，并保持 service 文件行数 ≤ 250。
- Tests:
  - 新增 `ai-pic-backend/tests/unit/services/ai/test_episode_generation_strict.py` 覆盖 episode_count mismatch → repair success/failed。
  - 更新 `ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py`，断言 raw/normalized 会进入 `Task.parameters.agent_run`。
- Docs:
  - 更新 `tasks.md`：Phase 1（严格结构化输出 + repair）标记完成。

## Validation

- `pre-commit run --files ai-pic-backend/app/services/ai/episodes.py ai-pic-backend/app/api/v1/endpoints/episodes/async_tasks.py ai-pic-backend/app/services/episode/episode_generation_service.py ai-pic-backend/app/services/episode/episode_generation_utils.py ai-pic-backend/tests/unit/services/ai/test_episode_generation_strict.py ai-pic-backend/tests/unit/services/test_task_agent_run_persistence.py tasks.md`
- `./docker/build_prod_images.sh`（buildx build+push；tag 为执行时的 HEAD: `c6ae021`）
- Chrome E2E（docker 环境，账号 `geyunfei / Gyf@845261`）：
  - 成功 case：Story `http://localhost:8089/stories/6131b3857ce9413b9a1fbc6a5b23d1f8` → 生成剧集 `episode_count=2`（异步）→ 任务 `5860` COMPLETED，result `episodes:125,126`，任务详情可见 `agent_run.outline/agent_run.episodes` 审计信息。
  - 失败 case：同一 Story → 生成剧集 `episode_count=3` 且选择 `model=google:gemini-1.0-pro` → 任务 `5861` FAILED（error.message=`AI剧集生成失败`），Story “剧集列表”仍为 `2` 集（无新增 Episode 落库）。

## Next Steps

- Phase 2：定义并落地 `StoryContextPack/EpisodeContextPack`（并把 used_context 写入 agent_run）。
- Phase 3：Story→Episode readiness 检查（阻断生成 + 一键补齐）。

## Linked Commits

- (pending)
