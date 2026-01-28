---
id: 2026-01-28T10-44-03Z-story-generation-strict-validation
date: "2026-01-28T10:44:03Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, story, structured-output, docs]
related_paths:
  - ai-pic-backend/app/services/ai/structured_output.py
  - ai-pic-backend/app/services/ai/story_outline.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/services/story/story_outline_normalizer.py
  - ai-pic-backend/app/services/story/story_generation_utils.py
  - docs/design/story-episode-generation-quality.md
  - docs/README.md
summary: "Story generation now enforces strict schema validation + repair, and surfaces agent_run audit data in tasks UI."
---

## User Prompt

- 现在故事生成/剧集生成逻辑过于简陋：缺少上下文管理、逻辑校验、检查验证；按 `tasks.md` 推进并保证原子化提交。
- 先把“严格结构化输出 + repair”落到故事生成，并能在 Docker 环境里实际跑通、在任务页可审计。

## Goals

- 让故事大纲生成按 `StoryOutlineModel` 做严格校验，不再把“猜出来的文本”落库。
- 为 AI 输出提供有限次数的 repair（同一 JSON schema），失败则明确报错。
- 在 `/tasks` 里可直接看到本次生成的 `agent_run`（provider/model/usage + raw/normalized/errors/repairs）。
- 同步更新设计文档与 docs 索引。

## Changes

- Backend: `structured_output` 支持 repair 使用独立 `repair_system_prompt`，并输出可审计的 `first_attempt/repair_attempts` 元数据。
- Backend: 故事大纲生成（`StoryOutlineMixin`）接入 `generate_with_repair(...)`；兜底路径使用 `validate_payload(...)` 做 schema 校验。
- Backend: `StoryGenerationService` 持久化前强制执行严格 normalize（提取为 `normalize_story_outline_strict`），校验失败直接抛错。
- Backend: `agent_run` 补齐审计字段（`raw_content/normalized/validation_errors/repair_attempts/first_attempt`），用于任务页展示。
- Docs: 新增 `docs/design/story-episode-generation-quality.md`，并更新 `docs/README.md` 索引。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome (MCP) E2E:
  - 登录 `geyunfei / Gyf@845261`
  - `/stories` → `AI生成故事` → 填写标题并选择角色 → `创建异步任务`（提示任务 ID: 5859）
  - `/tasks` 中确认任务完成；展开详情可看到 `parameters.agent_run.normalized/raw_content/repair_attempts/...`

## Next Steps

- 按 `tasks.md` Phase 1/2/3 继续推进 episode generation 的严格 schema + repair + 上下文/就绪检查。
- 视频生成的 `provider_task_id` 超长报错：确认 DB 已应用对应 alembic migration，并重启 worker（独立原子任务）。

## Linked Commits

- (pending)
