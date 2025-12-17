---
id: 2025-12-17T03-24-05Z-mysql-default-fix
date: 2025-12-17T03:24:05Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/alembic/versions/b9b5c7e3a8d1_add_business_id_and_soft_delete.py
summary: "Fix MySQL syntax issue by removing replace(uuid(),'-','') server default in business_id migration"
---

## User Prompt

- 迁移在 MySQL 因 `server_default=replace(uuid(), '-', '')` 语法报错，请修复。

## Goals

- 去掉方言依赖的默认表达式，避免 MySQL 语法错误，改为后续回填生成 business_id。

## Changes

- 在 `b9b5c7e3a8d1_add_business_id_and_soft_delete.py` 中将 `default_expr` 固定为 `None`，不再在 DDL 里使用 `replace(uuid(), '-', '')`，业务 ID 由回填逻辑生成。

## Validation

- 未重跑迁移（需在容器内重新执行 `alembic upgrade head` 验证）。

## Next Steps

- 重新执行迁移；如再有错误请反馈日志。

## Linked Commits

- (pending)
