---
id: 2025-10-17T09-10-42Z-story-structure-canonical-erd
date: 2025-10-17T09:10:42Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, docs]
related_paths:
  - docs/story-structure-gap-analysis.md
summary: "Locked canonical relationships and column set for story_treatments through shots"
---

## User Prompt
锁定 story_treatments, story_step_outlines, scenes, scene_beats, shots 的 ERD 与字段列表。

## Goals
- 明确各层级之间的外键与生命周期关系。
- 为后续建模与迁移提供列级别定义和约束参考。

## Changes
- 更新 `docs/story-structure-gap-analysis.md`，新增 Canonical Entity Relationships 和各表字段定义表格。

## Validation
- 未运行自动化测试（文档-only 更新）。

## Next Steps
- 基于字段定义绘制正式 ER 图（PlantUML / Mermaid）供评审。
- 准备 Alembic 迁移草案和 JSON 提取脚本以验证可行性。

## Linked Commits
- (pending)

