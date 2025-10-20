---
id: 2025-10-20T07-00-00Z-story-structure-orm-models
date: 2025-10-20T07:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models, migrations]
related_paths:
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/models/__init__.py
  - ai-pic-backend/alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py
summary: "Add ORM models for normalized story structure tables and export them."
---

## User Prompt

按计划进行，保证提交的原子性；首先为规范化叙事结构添加 ORM 模型以对齐 Alembic 迁移。

## Goals

- 建立与迁移一致的 ORM 模型：`story_treatments`、`story_step_outlines`、`scenes`、`scene_beats`、`shots`。
- 定义必要的关系，避免与现有 `Script.scenes` JSON 字段命名冲突。
- 将新模型在 `models/__init__.py` 中导出，便于后续 schema、service、API 使用。

## Changes

- 新增文件 `ai-pic-backend/app/models/story_structure.py`：定义 `StoryTreatment`、`StoryStepOutline`、`Scene`、`SceneBeat`、`Shot` 模型及关系。
- 更新 `ai-pic-backend/app/models/__init__.py`：导出新模型。
- 关系设计要点：
  - `Scene.script` 使用 `backref="normalized_scenes"`，避免覆盖 `Script` 上的 JSON 字段 `scenes`。
  - `Shot.storyboard_image` 关联 `images.id`，与迁移保持一致。

## Validation

- 对照 `alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py` 字段与外键设计逐项核对。
- 本地运行 `pytest` 存在既有失败，与此次增量无直接关联；模型定义导入无语法/引用错误（静态检查通过）。

## Next Steps

- 添加 Pydantic Schemas 与 Service 层基础 CRUD。
- 增加最小读写 API（feature flag 可选）并在前端分镜页按需试读。
- 为新增模块补充针对性测试用例（模型与迁移兼容性）。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

