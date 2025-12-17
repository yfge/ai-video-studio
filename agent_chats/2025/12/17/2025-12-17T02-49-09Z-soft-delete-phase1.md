---
id: 2025-12-17T02-49-09Z-soft-delete-phase1
date: 2025-12-17T02:49:09Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/app/models/base.py
  - ai-pic-backend/app/models/user.py
  - ai-pic-backend/app/models/image.py
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/models/task.py
  - ai-pic-backend/alembic/versions/b9b5c7e3a8d1_add_business_id_and_soft_delete.py
summary: "Start Phase 1: add soft-delete/business_id mixin to models and migration scaffolding"
---

## User Prompt

- 用户要求为所有实体增加软删除和 `business_id`，关联切换到 business_id，regenerate 返回新 ID，并继续推进实施。

## Goals

- 引入统一的 soft-delete + business_id mixin，并让核心模型继承。
- 新增 Alembic 迁移，为主要业务表添加业务主键与软删字段和索引，并回填业务 ID。

## Changes

- 新建 `SoftDeleteBusinessMixin`（业务 ID 生成、软删字段与 helper），应用到用户、虚拟 IP、故事/剧集/剧本、故事结构、图片、任务等模型。
- 新增迁移 `b9b5c7e3a8d1`：为核心表添加 `business_id`、软删字段、索引，按 dialect 处理默认值并用 uuid4.hex 回填。

## Validation

- 未运行自动化测试（迁移编写阶段，后续需跑 pytest）。

## Next Steps

- 运行 `pytest` 验证迁移与模型改动。
- Phase 2: 为关联补充 `*_business_id` 双写/回填并调整唯一约束含 `is_deleted`。
- Phase 3: 删除/恢复改软删、regenerate 新记录落地并处理派生数据；前端切换 business_id。

## Linked Commits

- (pending)
