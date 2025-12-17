---
id: 2025-12-17T03-03-15Z-soft-delete-phase2-business-links
date: 2025-12-17T03:03:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/alembic/versions/dc3d7b9b2c41_add_business_fk_columns.py
summary: "Phase 2 start: add business_id link columns and migration to backfill"
---

## User Prompt

- 用户要求继续推进软删 + business_id，关联改为 business_id。

## Goals

- 为核心子表增加 `*_business_id` 关联列并在模型中暴露。
- 编写迁移为这些列回填父表的 `business_id` 并建立索引。

## Changes

- 模型新增 business 关联列：Episode→Story，Script→Episode，StoryCharacter→Story/VirtualIP，StoryStepOutline→Story/Episode/Treatment，Scene→Script/StepOutline/Environment，SceneBeat→Scene，Shot→Scene/SceneBeat，VirtualIPImage→VirtualIP，Task→target business_id。
- 新迁移 `dc3d7b9b2c41_add_business_fk_columns.py` 添加上述列及索引，并通过 JOIN/uuid4 回填。

## Validation

- 未运行测试（迁移/模型改动后续需跑 pytest；此前全量 pytest 超时，诊断接口用例因未授权保护而失败）。

## Next Steps

- 调整唯一约束含 `is_deleted`；新增默认查询过滤及软删/再生成语义；前端切换 business_id。
- 运行 pytest 并修复诊断接口认证问题后重跑。

## Linked Commits

- (pending)
