---
id: 2026-01-29T06-51-36Z-update-tasks-p0-roadmap
date: "2026-01-29T06:51:36Z"
participants: [human, codex]
models: [gpt-5]
tags: [meta, planning, tasks]
related_paths:
  - tasks.md
summary: "Expanded tasks.md with P0 roadmap for aspect ratio, media persistence, and generation quality."
---

## User Prompt

把 1/2/3 详细任务列出来更新 `tasks.md`，并按 `tasks.md` 推进，保证原子化提交与及时更新文档。

## Goals

- 把本轮 P0 需求拆成可执行的子任务：画幅规格、生成资产持久化统一抽象、生成质量闭环（上下文/校验/人物集中管理）。
- 明确默认值与可覆盖策略，并补充对应的端到端验证要求（Chrome + Docker）。

## Changes

- 更新 `tasks.md`：
  - 新增 `P0: 用户本轮需求（画幅/资产/生成质量）` 分区，并按 1/2/3 拆解为可执行 checklist。
  - 明确画幅：仅支持 `9:16`/`16:9`、默认 `9:16`、允许本次任务临时覆盖（不落库）。
  - 补充 media persistence 统一抽象与 `provider_task_id` 长度问题的修复任务。
  - 补充全流程 E2E 验证要求（deepseek 文生文 / google banana pro 生图 / google veo3 生视频）。

## Validation

- 文档变更：无代码路径变更；待后续实现任务时再补 `pytest`/`npm run lint`/Chrome E2E 记录。

## Next Steps

- 按 `tasks.md` 从 1) 画幅规格开始实现，保持每个原子任务独立提交并附带对应 `agent_chats` 记录。

## Linked Commits

- (pending)
