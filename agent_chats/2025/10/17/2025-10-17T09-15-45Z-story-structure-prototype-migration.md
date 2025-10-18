---
id: 2025-10-17T09-15-45Z-story-structure-prototype-migration
date: 2025-10-17T09:15:45Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py
  - ai-pic-backend/scripts/prototype_story_structure_migration.py
  - docs/story-structure-gap-analysis.md
summary: "Drafted normalized story structure migration and sample JSON extractor"
---

## User Prompt
Prototype Alembic migrations and JSON extraction scripts against sample data验证设计。

## Goals
- 创建新的叙事结构核心表的 Alembic 草案。
- 实现脚本以现有 JSON 样本生成即将落库的数据结构。
- 在文档中标注原型资产，方便后续评审。

## Changes
- 新增 `ai-pic-backend/alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py`，定义 `story_treatments`、`story_step_outlines`、`scenes`、`scene_beats`、`shots` 表及唯一约束。
- 新增 `ai-pic-backend/scripts/prototype_story_structure_migration.py`，基于样例 Story/Episode/Script JSON 输出归一化记录。
- 更新 `docs/story-structure-gap-analysis.md`，追加 Prototype Assets 章节记录原型文件。

## Validation
- 运行 `python ai-pic-backend/scripts/prototype_story_structure_migration.py` 输出结构化样例，验证提取逻辑。

## Next Steps
- 结合真实数据库样本扩展提取脚本，增加插入/回滚验证。
- 依据该原型生成正式 ER 图，并评审字段命名与约束策略。

## Linked Commits
- (pending)

