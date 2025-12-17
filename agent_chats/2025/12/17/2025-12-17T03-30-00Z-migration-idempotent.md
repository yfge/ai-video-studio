---
id: 2025-12-17T03-30-00Z-migration-idempotent
date: 2025-12-17T03:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/alembic/versions/b9b5c7e3a8d1_add_business_id_and_soft_delete.py
summary: "Make business_id/soft-delete migration idempotent to avoid duplicate column errors"
---

## User Prompt

- 迁移在 MySQL 报 `(1060) Duplicate column name 'is_deleted'`，需要在容器侧修复。

## Goals

- 让 `b9b5c7e3a8d1_add_business_id_and_soft_delete.py` 在重复执行或部分执行后可安全重跑，避免重复列/索引错误。

## Changes

- 在迁移中使用 `inspector` 检查现有列/索引，已存在则跳过 `add_column` / `create_index`，保持回填逻辑不变。

## Validation

- 未在容器内重新跑迁移（需执行 `alembic upgrade head` 验证）。

## Next Steps

- 重新运行迁移；如再有报错，请反馈。

## Linked Commits

- (pending)
