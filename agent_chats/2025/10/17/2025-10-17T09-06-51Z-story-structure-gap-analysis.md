---
id: 2025-10-17T09-06-51Z-story-structure-gap-analysis
date: 2025-10-17T09:06:51Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, docs]
related_paths:
  - docs/story-structure-gap-analysis.md
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/schemas/script.py
summary: "Documented gaps between current story data model and Treatment/Scene industry structure"
---

## User Prompt

检查 task.md 的内容，并按照任务拆分逐步推进，确保最小化提交。

## Goals

- 审阅现有 Story → Episode → Script 模型结构。
- 输出与工业级 Treatment / Step Outline / Scene / Shot 结构的对比文档。

## Changes

- 新增 `docs/story-structure-gap-analysis.md`，总结当前数据模型并对齐行业叙事层级。
- 创建所需 `docs/` 目录。

## Validation

- 未运行自动化测试（文档更新，无代码执行路径变更）。

## Next Steps

- 基于文档中列出的差距细化 ER 图和字段定义。
- 明确版本化策略及迁移兼容方案后，启动 Alembic 迁移设计。

## Linked Commits

- (pending)
