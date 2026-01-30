---
id: 2025-10-20T07-45-00Z-fix-sqlalchemy-metadata-reserved
date: 2025-10-20T07:45:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, fix]
related_paths:
  - ai-pic-backend/app/models/story_structure.py
summary: "Rename reserved attribute 'metadata' to 'extra_metadata' columns in ORM models."
---

## User Prompt

在导入新端点模块时遇到 SQLAlchemy Declarative API 保留名冲突问题，需要修正模型定义。

## Goals

- 避免与 Declarative Base 的 `metadata` 冲突，保持与迁移的列名 `metadata` 对齐。

## Changes

- 将 `StoryTreatment/StoryStepOutline/Scene/SceneBeat/Shot` 模型上的 `metadata` 属性重命名为 `extra_metadata`，并显式指定列名为 `"metadata"`，例如：`extra_metadata = Column("metadata", JSON)`。

## Validation

- 脚本导入校验：`import app.api.v1.endpoints.story_structure` 成功；模块 `router` 存在。

## Next Steps

- 继续对接 API 与前端试读。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
