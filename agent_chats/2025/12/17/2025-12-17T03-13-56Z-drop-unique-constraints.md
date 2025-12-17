---
id: 2025-12-17T03-13-56Z-drop-unique-constraints
date: 2025-12-17T03:13:56Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/app/models/base.py
  - ai-pic-backend/app/models/user.py
  - ai-pic-backend/app/models/virtual_ip.py
  - ai-pic-backend/alembic/versions/f2d1a3c4b5e6_drop_unique_constraints.py
summary: "Removed unique constraints (business_id and key fields) and added migration to recreate indexes without uniqueness"
---

## User Prompt

- 用户要求去掉所有唯一约束，只保留索引，由业务层做重复检测。

## Goals

- 取消模型层的唯一约束，并提供迁移移除数据库中的唯一索引。

## Changes

- 模型：移除 `business_id`/用户名/邮箱/虚拟 IP 名称的 `unique=True`（保留索引）。
- 迁移：`f2d1a3c4b5e6_drop_unique_constraints.py` 删除 business_id 索引和核心业务索引的唯一性，并重建为非唯一；故事结构内的唯一索引也改为非唯一。

## Validation

- 未运行测试（迁移/模型调整后需在后续集中验证）。

## Next Steps

- 继续添加软删过滤、删除/再生成语义调整，并在后续运行 pytest 验证整体行为。

## Linked Commits

- (pending)
